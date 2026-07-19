"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from .recommender import (
    load_songs,
    recommend_songs,
    recommend_songs_diverse,
    STRATEGIES,
)

try:
    from tabulate import tabulate
except ImportError:  # tabulate not installed yet
    tabulate = None

# Pick a ranking mode here. Options: "Balanced", "Genre-First", "Mood-First",
# "Energy-Focused" (see STRATEGIES in recommender.py).
STRATEGY = "Balanced"

# When True, penalize repeated artists/genres in the top-k (recommend_songs_diverse).
DIVERSITY_MODE = False


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")
    print(f"Ranking strategy: {STRATEGY}  (options: {', '.join(STRATEGIES)})")
    print(f"Diversity mode: {DIVERSITY_MODE}")

    high_energy_pop = {"genre": "pop", "mood": "happy", "energy": 0.9}
    chill_lofi = {"genre": "lofi", "mood": "chill", "energy": 0.3}
    deep_intense_rock = {"genre": "rock", "mood": "intense", "energy": 0.9}

    sad_but_hyper = {"genre": "pop", "mood": "sad", "energy": 0.95}
    ghost_profile = {"genre": "polka", "mood": "euphoric", "energy": 0.5}
    overclocked = {"genre": "rock", "mood": "intense", "energy": 2.0}
    wrong_energy_right_genre = {"genre": "classical", "mood": "intense", "energy": 1.0}

    profiles = [
        ("High-Energy Pop", high_energy_pop),
        ("Chill Lofi", chill_lofi),
        ("Deep Intense Rock", deep_intense_rock),
        ("Sad But Hyper (conflict)", sad_but_hyper),
        ("Ghost Profile (no matches)", ghost_profile),
        ("Overclocked (energy=2.0)", overclocked),
        ("Wrong Energy Right Genre", wrong_energy_right_genre),
    ]

    if tabulate is None:
        print(
            "\nNote: the 'tabulate' package is not installed — falling back to plain text.\n"
            "Install it with:  pip install tabulate\n"
        )

    for name, user_prefs in profiles:
        print(f"\n=== {name} ===\n")
        if DIVERSITY_MODE:
            recommendations = recommend_songs_diverse(user_prefs, songs, k=5, strategy=STRATEGY)
        else:
            recommendations = recommend_songs(user_prefs, songs, k=5, strategy=STRATEGY)

        rows = [
            (rank, song["title"], f"{score:.2f}", explanation)
            for rank, (song, score, explanation) in enumerate(recommendations, start=1)
        ]
        headers = ["Rank", "Title", "Score", "Reasons"]

        if tabulate is not None:
            print(tabulate(rows, headers=headers, tablefmt="github"))
        else:
            # Plain-text fallback when tabulate isn't available.
            for rank, title, score, explanation in rows:
                print(f"{rank}. {title} - Score: {score}")
                print(f"   Because: {explanation}")
        print()


if __name__ == "__main__":
    main()
