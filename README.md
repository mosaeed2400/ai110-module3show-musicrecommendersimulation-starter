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

**Expected bias:** Because genre and mood are exact-match categorical checks worth significant flat points, this system may over-prioritize genre matches even when a song's actual energy profile is a poor fit — for example, any "pop" song scores +2.0 regardless of how different its energy actually is from the user's target. This is a bias I plan to investigate further during testing in Phase 4.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows
```

2. Install dependencies:

```bash
   pip install -r requirements.txt
```

3. Run the app:

```bash
   python3 -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

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

<!-- TODO (Phase 4): Document the experiments you ran. -->

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or acousticness to the score
- How did your system behave for different types of users (e.g., "High-Energy Pop," "Chill Lofi," "Deep Intense Rock," and any adversarial/edge-case profiles)

---

## Limitations and Risks

<!-- TODO (Phase 4, Step 4): Summarize limitations discovered during testing. -->

Some known limitations of this design going in:
- The catalog is very small (18 songs), so recommendations may feel repetitive regardless of scoring logic
- It has no understanding of lyrics, language, or subjective quality — only numeric and categorical attributes
- Genre and mood are broad categorical labels that can mask real differences between songs (e.g., two "intense" songs can have very different valence), which may cause the system to over- or under-value certain matches
- With no other users' behavior to draw from, the system can't discover songs outside a user's stated preferences — it has no serendipity, unlike collaborative filtering
- The project has two parallel scoring implementations (OOP and functional) that currently use slightly different recipes, which could confuse a future maintainer if not kept in sync

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

<!-- TODO (Phase 5): Write 1-2 paragraphs here about what you learned:
- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this -->