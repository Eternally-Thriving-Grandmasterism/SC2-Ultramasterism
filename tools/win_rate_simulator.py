"""Random toy: flips a weighted coin ``games`` times and prints the share of "wins".

This is not a measure of anything. It does not model StarCraft II, a player or
a bot; the printed number only reflects the ``win_probability`` you pass in
plus random noise. The default of 0.5 is a neutral coin flip.
"""

import random


def simulate_matchup(win_probability=0.5, games=1000, rng=None):
    """Return the share of random "wins" out of ``games`` weighted coin flips."""
    rng = rng or random
    wins = sum(rng.random() < win_probability for _ in range(games))
    return wins / games


if __name__ == "__main__":
    share = simulate_matchup()
    print(
        f"Random toy (not a measure): {share * 100:.1f}% of {1000} coin flips "
        "came up 'win' at p=0.5"
    )
