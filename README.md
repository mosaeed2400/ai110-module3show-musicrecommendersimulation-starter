# 🎵 Music Recommender Simulation

## Project Summary

This project is a simplified simulation of how music platforms like Spotify or YouTube predict what you'll want to hear next. My version is a content-based recommender: it doesn't know anything about other users, only about the songs themselves. It represents each song as a set of numeric and categorical attributes (genre, mood, energy, valence, acousticness), compares those attributes against a user's stated taste profile, and calculates a weighted score for every song in the catalog. The highest-scoring songs are returned as recommendations, along with a plain-language breakdown of why each one was picked.

---

## How The System Works

Real-world recommendation systems generally rely on two approaches. **Collaborative filtering** predicts what a user will like based on patterns across many other users (e.g., "people who liked what you liked also liked this"). **Content-based filtering** predicts recommendations purely from a song's own attributes — genre, tempo, mood, energy — compared against what a specific user tends to enjoy. Big platforms like Spotify blend both approaches, but since this project only has a static catalog and one user profile (no cross-user data), it implements a pure content-based recommender.

**Features used by `Song`:**
- `genre` — categorical (e.g., pop, lofi, rock)
- `mood` — categorical (e.g., happy, chill, intense)
- `energy` — numeric, 0.0–1.0 scale
- `valence` — numeric, 0.0–1.0 scale (a "positivity" measure independent of energy)
- `acousticness` — numeric, 0.0–1.0 scale

I initially considered dropping `acousticness` since it was almost perfectly inversely correlated with `energy` in this dataset (energy + acousticness ≈ 1.0 for every song). I planned to use `valence` as a bonus signal instead, since it catches distinctions `mood` alone misses — for example, two songs both tagged "intense" can have very different valence scores (one aggressive/dark, one upbeat/motivating).

However, during implementation I discovered `tests/test_recommender.py` requires a specific `UserProfile` shape with a `likes_acoustic: bool` field rather than `target_valence`. Rather than break the required tests, I adapted my recipe: the graded `Recommender` class uses `likes_acoustic` as a simple boolean preference (do you want acoustic songs or not) instead of a numeric valence target. This is a good example of a real constraint — a recommender's scoring logic has to work within whatever data contract the rest of the system (or its tests) expects, even if a different design was originally planned.

**Two parallel implementations exist in this project:**
1. **OOP path** (`Song`, `UserProfile`, `Recommender` class) — required by the test suite
2. **Functional path** (`load_songs`, `score_song`, `recommend_songs`) — used by the CLI in `main.py`, working on plain dictionaries

**Information stored in `UserProfile` (OOP path):**
- `favorite_genre`
- `favorite_mood`
- `target_energy`
- `likes_acoustic` (boolean)

**How the `Recommender` class computes a score:**
- **+2.0** if `genre` exactly matches `favorite_genre`
- **+1.0** if `mood` exactly matches `favorite_mood`
- **Up to +1.5** based on energy similarity: `(1 - abs(song.energy - target_energy)) * 1.5`
- **+1.0** if `likes_acoustic` is `True` and the song's `acousticness > 0.6`
- **+0.5** if `likes_acoustic` is `False` and the song's `acousticness < 0.4`

**How the functional `score_song`/`recommend_songs` compute a score (used by the CLI):**
- **+2.0** if `genre` matches
- **+1.0** if `mood` matches
- **Up to +1.5** based on energy similarity, same closeness formula as above

Both paths return a numeric score plus a list of plain-language reasons (e.g., `"genre match (+2.0)"`, `"energy close to target (+1.4)"`) so a user can see *why* a song was recommended, not just that it was.

**How recommendations are chosen:**
Each implementation runs its scoring function across every song in the catalog — this is necessary because a single song's score is meaningless in isolation; it only matters relative to every other song's score. Once every song has been scored, the list is sorted from highest to lowest (using `.sort()`, since the scored list is temporary and local to the function — no need to preserve the original order or allocate a second list), and the top `k` results are returned as the final recommendations.

**Example User Profile (functional/CLI path):**
```python
user_prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}
```

**Example User Profile (OOP/tested path):**
```python
user = UserProfile(
    favorite_genre="pop",
    favorite_mood="happy",
    target_energy=0.8,
    likes_acoustic=False,
)
```

**Finalized Algorithm Recipe:**

| Feature | Rule | Max points |
|---|---|---|
| `genre` | exact match | +2.0 |
| `mood` | exact match | +1.0 |
| `energy` | `(1 - abs(song.energy - target_energy)) * 1.5` | up to +1.5 |
| `acousticness` (OOP path only) | bonus/penalty based on `likes_acoustic` | +1.0 or +0.5 |

Max possible score (OOP path): 5.5 points
Max possible score (functional/CLI path): 4.5 points

**Expected bias:** Because genre and mood are exact-match categorical checks worth significant flat points, this system may over-prioritize genre matches even when a song's actual energy profile is a poor fit — for example, any "pop" song scores +2.0 regardless of how different its energy actually is from the user's target. This bias was confirmed during Phase 4 testing — see `model_card.md` for the full analysis.

---

## Optional Extensions

Beyond the core project, I implemented all four optional extensions:

1. **Advanced Song Features** — added `popularity`, `release_decade`, `explicit`, `vocal_type`, and `detailed_mood_tags` to the dataset, with an optional popularity-similarity scoring bonus.
2. **Multiple Scoring Modes** — a Strategy pattern (`STRATEGY` constant in `main.py`) lets you switch between Balanced, Genre-First, Mood-First, and Energy-Focused ranking, all sharing one scoring function via configurable weights.
3. **Diversity and Fairness Logic** — a `DIVERSITY_MODE` toggle in `main.py` penalizes repeated artists/genres in the top-k results, directly addressing the genre-imbalance bias documented in `model_card.md`.
4. **Visual Summary Table** — CLI output renders as a formatted table (via `tabulate`) when the package is installed, with a graceful plain-text fallback if it isn't.

Full prompts, agent-generated changes, and manual verification notes for all four are documented in [`ai_interactions.md`](ai_interactions.md).

---

## Getting Started

### Setup

1. Create a virtual environment (recommended):

```bash
   python3 -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows
```

2. Install dependencies (includes `tabulate` for formatted table output):

```bash
   pip install -r requirements.txt
```

3. Run the app:

```bash
   python3 -m src.main
```

To try the optional extensions, edit the `STRATEGY` and `DIVERSITY_MODE` constants near the top of `src/main.py`.

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

*Note: this output reflects the core project's default behavior (before the "Visual Summary Table" extension was added). With `tabulate` installed, output now renders as a formatted table — see `ai_interactions.md` for a rendered example.*

```
Loaded songs: 18

Top recommendations:

Sunrise City - Score: 4.47
Because: genre match (+2.0), mood match (+1.0), energy close to target (+1.5)

Gym Hero - Score: 3.30
Because: genre match (+2.0), energy close to target (+1.3)

Rooftop Lights - Score: 2.44
Because: mood match (+1.0), energy close to target (+1.4)

Night Drive Loop - Score: 1.42
Because: energy close to target (+1.4)

Neon Uprising - Score: 1.35
Because: energy close to target (+1.4)
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

I tested the system with 3 standard profiles ("High-Energy Pop," "Chill Lofi," "Deep Intense Rock") plus 4 adversarial edge-case profiles designed to probe for weaknesses (a nonexistent mood, a genre/mood combo matching nothing in the catalog, an out-of-range energy value, and a genre-vs-fit conflict test). Full terminal output for all 7 profiles is documented in `model_card.md`'s Appendix.

**Weight Shift experiment:** I halved the genre weight (2.0 → 1.0) and doubled the energy weight (1.5 → 3.0) to test sensitivity. Across all 7 profiles, this compressed score margins everywhere and actually changed the top-5 ranking order in 2 of them. The clearest effect: Gym Hero (a strong mood/energy match but wrong genre) closed its score gap to Storm Runner from 2.02 points down to 1.06 — confirming that genre's flat +2.0 bonus was suppressing otherwise-strong matches. The tradeoff: Autumn Sonata, the catalog's only classical song, dropped out of the top 5 entirely once its genre bonus was halved, since its energy fit was poor. **Conclusion:** the reweighting made results different, not simply more accurate — it's a real tradeoff between genre fidelity and overall vibe similarity. Full before/after data is in `model_card.md`.

**On genre coverage:** since 13 of the catalog's 15 genres appear in only one song, fans of underrepresented genres (rock, jazz, classical, country, etc.) can never get more than one true genre match in their top 5, regardless of any weight change — this is a data limitation, not a tuning problem.

---

## Limitations and Risks

Testing surfaced several concrete weaknesses beyond the ones anticipated at design time:

- **The catalog is very small (18 songs) and genre coverage is thin** — 13 of 15 genres appear in only one song, so the system can't distinguish "likes this genre" from "likes this one song," and niche-genre fans structurally cannot receive a fully genre-coherent top 5.
- **Genre acts as a flat, binary bonus with no partial credit and no concept of similarity** — "pop" vs. "rock" scores identically to "pop" vs. "polka," even though some genres are much closer neighbors than others. This can let a poor overall fit beat a near-perfect mood/energy match, purely on a categorical label (confirmed directly: see the Gym Hero vs. Storm Runner case in `model_card.md`).
- **There is no input validation.** An out-of-range energy value (e.g., 2.0) produces literal negative scores and a broken-looking explanation string (e.g., `"energy close to target (+-0.1)"`) instead of being rejected or clamped.
- **Genre/mood values not present in the dataset fail silently** rather than raising an error or warning — the system confidently returns results even when a stated preference matched nothing at all.
- **Some preference combinations are impossible to satisfy no matter how the weights are tuned** — e.g., every acoustic song in the catalog is also low-energy, so a "loud and acoustic" listener is asking for something the data cannot provide.
- **`tempo_bpm`, `valence`, and `danceability` are loaded from the CSV but never actually used in scoring**, in either the OOP or functional path — a listener who cares about danceability has no way to express that preference, even though the data already exists.
- It has no understanding of lyrics, language, or subjective quality — only numeric and categorical attributes.
- With no other users' behavior to draw from, the system can't discover songs outside a user's stated preferences — it has no serendipity, unlike collaborative filtering.
- The project has two parallel scoring implementations (OOP and functional) that use slightly different recipes (the functional/CLI path doesn't use acousticness at all), which could confuse a future maintainer if not kept in sync.

The full bias analysis, including a dataset-level check for systemic issues, is documented in `model_card.md`, Section 6.

---

## Reflection

This project taught me that a scoring system can be completely "correct" by its own
math and still produce results that feel wrong — a song can lose decisively not
because it's a poor match, but because of a structural blind spot in how the
weights are balanced (see Gym Hero vs. Storm Runner in the Model Card). AI tools
were most useful when I asked them to actively try to break my own logic with
adversarial profiles, rather than just build forward — but I also learned to verify
their claims against real output rather than trusting them outright, since one
early claim about genre "always" dominating didn't fully hold up once I ran the
actual numbers.

The full reflection, including what surprised me and what I'd change next, is in
[model_card.md](model_card.md), Section 9.

Read the complete Model Card here: [**Model Card**](model_card.md)