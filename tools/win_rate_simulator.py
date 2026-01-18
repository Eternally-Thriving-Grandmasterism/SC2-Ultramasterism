import random

def simulate_matchup(wins_human=0.98, games=1000):  # Your edge :)
    human_wins = sum(random.random() < wins_human for _ in range(games))
    print(f"Ultramaster Win Rate: {human_wins / games * 100}% over {games} sims")

simulate_matchup()
