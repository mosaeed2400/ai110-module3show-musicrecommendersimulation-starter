import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def _score_song(self, user: UserProfile, song: Song) -> Tuple[float, List[str]]:
        score = 0.0
        reasons: List[str] = []

        if song.genre == user.favorite_genre:
            score += 2.0
            reasons.append("genre match (+2.0)")

        if song.mood == user.favorite_mood:
            score += 1.0
            reasons.append("mood match (+1.0)")

        energy_points = (1 - abs(song.energy - user.target_energy)) * 1.5
        score += energy_points
        reasons.append(f"energy close to target (+{energy_points:.1f})")

        if user.likes_acoustic and song.acousticness > 0.6:
            score += 1.0
            reasons.append("acoustic match (+1.0)")
        elif not user.likes_acoustic and song.acousticness < 0.4:
            score += 0.5
            reasons.append("non-acoustic match (+0.5)")

        return score, reasons

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        scored = [(self._score_song(user, song)[0], song) for song in self.songs]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [song for _, song in scored[:k]]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        _, reasons = self._score_song(user, song)
        return ", ".join(reasons)

def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py
    """
    songs = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["id"] = int(row["id"])
            for field in ("energy", "tempo_bpm", "valence", "danceability", "acousticness"):
                row[field] = float(row[field])
            row["popularity"] = int(row["popularity"])
            row["explicit"] = row["explicit"].strip().lower() == "true"
            row["detailed_mood_tags"] = [
                tag for tag in row["detailed_mood_tags"].split(";") if tag
            ]
            songs.append(row)
    return songs

# --- Ranking strategies ----------------------------------------------------
# A "strategy" is just a weight profile: how many points each scoring component
# contributes. The scoring logic itself lives once in score_song(); strategies
# only vary these weights, so there is no duplicated logic to keep in sync.
DEFAULT_WEIGHTS: Dict[str, float] = {
    "genre": 2.0, "mood": 1.0, "energy": 1.5, "popularity": 0.5,
}

STRATEGIES: Dict[str, Dict[str, float]] = {
    "Balanced": DEFAULT_WEIGHTS,
    "Genre-First": {"genre": 3.0, "mood": 1.0, "energy": 1.0, "popularity": 0.5},
    "Mood-First": {"genre": 1.0, "mood": 3.0, "energy": 1.0, "popularity": 0.5},
    "Energy-Focused": {"genre": 1.0, "mood": 1.0, "energy": 3.0, "popularity": 0.5},
}

def score_song(user_prefs: Dict, song: Dict, weights: Optional[Dict[str, float]] = None) -> Tuple[float, List[str]]:
    """
    Scores a song dict against user_prefs (genre, mood, energy, popularity) and returns (score, reasons).
    The optional `weights` profile controls each component's contribution; defaults to DEFAULT_WEIGHTS.
    Required by recommend_songs() and src/main.py
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    score = 0.0
    reasons: List[str] = []

    if song["genre"] == user_prefs["genre"]:
        score += weights["genre"]
        reasons.append(f"genre match (+{weights['genre']:.1f})")

    if song["mood"] == user_prefs["mood"]:
        score += weights["mood"]
        reasons.append(f"mood match (+{weights['mood']:.1f})")

    energy_points = (1 - abs(song["energy"] - user_prefs["energy"])) * weights["energy"]
    score += energy_points
    reasons.append(f"energy close to target (+{energy_points:.1f})")

    # Optional: reward songs near a target popularity, if the user specified one.
    # Skipped when target_popularity is absent, to stay backward-compatible.
    if user_prefs.get("target_popularity") is not None:
        if abs(song["popularity"] - user_prefs["target_popularity"]) <= 20:
            score += weights["popularity"]
            reasons.append(f"popularity match (+{weights['popularity']:.1f})")

    return score, reasons

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5, strategy: str = "Balanced") -> List[Tuple[Dict, float, str]]:
    """
    Scores every song with score_song and returns the top k as (song, score, explanation) tuples.
    `strategy` selects a weight profile by name from STRATEGIES (defaults to "Balanced").
    Required by src/main.py
    """
    if strategy not in STRATEGIES:
        raise ValueError(f"Unknown strategy {strategy!r}. Available: {', '.join(STRATEGIES)}")
    weights = STRATEGIES[strategy]

    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song, weights)
        scored.append((song, score, ", ".join(reasons)))

    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:k]

def recommend_songs_diverse(user_prefs: Dict, songs: List[Dict], k: int = 5, strategy: str = "Balanced") -> List[Tuple[Dict, float, str]]:
    """
    Like recommend_songs, but builds the top-k greedily one song at a time and
    penalizes candidates that repeat an already-selected artist (-0.75) or genre
    (-0.5), so the results aren't dominated by the same artist/genre.
    """
    if strategy not in STRATEGIES:
        raise ValueError(f"Unknown strategy {strategy!r}. Available: {', '.join(STRATEGIES)}")
    weights = STRATEGIES[strategy]

    # Score every song once against the chosen strategy.
    candidates = []
    for song in songs:
        base, reasons = score_song(user_prefs, song, weights)
        candidates.append({"song": song, "base": base, "reasons": reasons})

    selected: List[Tuple[Dict, float, str]] = []
    seen_artists = set()
    seen_genres = set()

    for _ in range(min(k, len(candidates))):
        best = None
        best_adj = None
        best_penalties: List[str] = []

        for cand in candidates:
            adj = cand["base"]
            penalties: List[str] = []
            if cand["song"]["artist"] in seen_artists:
                adj -= 0.75
                penalties.append("artist repeat (-0.75)")
            if cand["song"]["genre"] in seen_genres:
                adj -= 0.5
                penalties.append("genre repeat (-0.5)")

            if best is None or adj > best_adj:
                best = cand
                best_adj = adj
                best_penalties = penalties

        candidates.remove(best)
        seen_artists.add(best["song"]["artist"])
        seen_genres.add(best["song"]["genre"])
        explanation = ", ".join(best["reasons"] + best_penalties)
        selected.append((best["song"], best_adj, explanation))

    return selected

# --- EXPERIMENT: reweighted scoring ---------------------------------------
# Hypothesis: genre's flat +2.0 lets a worse mood/energy fit win purely on
# genre. Reweight to reduce genre's dominance and reward close energy more.
#   genre match:      +1.0 (halved from 2.0)
#   mood match:       +1.0 (unchanged)
#   energy similarity: up to +3.0 (doubled from 1.5)
# Max possible score = 1.0 + 1.0 + 3.0 = 5.0.
# The originals above are unchanged; the CLI still calls them.

def score_song_experimental(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Experimental reweighting of score_song (genre +1.0, mood +1.0, energy up to +3.0).
    """
    score = 0.0
    reasons: List[str] = []

    if song["genre"] == user_prefs["genre"]:
        score += 1.0
        reasons.append("genre match (+1.0)")

    if song["mood"] == user_prefs["mood"]:
        score += 1.0
        reasons.append("mood match (+1.0)")

    energy_points = (1 - abs(song["energy"] - user_prefs["energy"])) * 3.0
    score += energy_points
    reasons.append(f"energy close to target (+{energy_points:.1f})")

    return score, reasons

def recommend_songs_experimental(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Experimental variant of recommend_songs using score_song_experimental weights.
    """
    scored = []
    for song in songs:
        score, reasons = score_song_experimental(user_prefs, song)
        scored.append((song, score, ", ".join(reasons)))

    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:k]
