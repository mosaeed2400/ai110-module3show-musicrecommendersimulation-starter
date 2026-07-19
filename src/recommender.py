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
            songs.append(row)
    return songs

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Scores a song dict against user_prefs (genre, mood, energy match) and returns (score, reasons).
    Required by recommend_songs() and src/main.py
    """
    score = 0.0
    reasons: List[str] = []

    if song["genre"] == user_prefs["genre"]:
        score += 2.0
        reasons.append("genre match (+2.0)")

    if song["mood"] == user_prefs["mood"]:
        score += 1.0
        reasons.append("mood match (+1.0)")

    energy_points = (1 - abs(song["energy"] - user_prefs["energy"])) * 1.5
    score += energy_points
    reasons.append(f"energy close to target (+{energy_points:.1f})")

    return score, reasons

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Scores every song with score_song and returns the top k as (song, score, explanation) tuples.
    Required by src/main.py
    """
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        scored.append((song, score, ", ".join(reasons)))

    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:k]

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
