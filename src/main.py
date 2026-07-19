"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from .recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

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

    for name, user_prefs in profiles:
        print(f"\n=== {name} ===\n")
        recommendations = recommend_songs(user_prefs, songs, k=5)
        for rec in recommendations:
            # You decide the structure of each returned item.
            # A common pattern is: (song, score, explanation)
            song, score, explanation = rec
            print(f"{song['title']} - Score: {score:.2f}")
            print(f"Because: {explanation}")
            print()


if __name__ == "__main__":
    main()
