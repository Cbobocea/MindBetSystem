# simulate_from_dataorg.py

import random
import time

# === Configuration Constants ===
HOME_ADVANTAGE_BONUS = 20            # Extra boost for home team based on traditional advantage
MINIMUM_DRAW_PROBABILITY = 5          # Minimum draw chance even if teams are very different
DEFAULT_HOME_WIN_PROB = 45            # Default fallback Home Win probability
DEFAULT_DRAW_PROB = 30                # Default fallback Draw probability
DEFAULT_AWAY_WIN_PROB = 25             # Default fallback Away Win probability

def simulate_match_full(match, standings, n_simulations=1000):
    """
    Simulate a match outcome dynamically based on team standings (points).
    Tracks win/draw/lose, scorelines, goals, BTTS, over/under 2.5, confidence.
    """

    home_team = match['home_team']
    away_team = match['away_team']

    home_info = standings.get(home_team)
    away_info = standings.get(away_team)

    if home_info and away_info:
        home_points = home_info["points"]
        away_points = away_info["points"]

        total_points = home_points + away_points

        if total_points == 0:
            home_win_prob = DEFAULT_HOME_WIN_PROB
            draw_prob = DEFAULT_DRAW_PROB
            away_win_prob = DEFAULT_AWAY_WIN_PROB
        else:
            home_win_prob = int((home_points / total_points) * 60) + HOME_ADVANTAGE_BONUS
            away_win_prob = int((away_points / total_points) * 60) + HOME_ADVANTAGE_BONUS
            draw_prob = 100 - (home_win_prob + away_win_prob)

            if draw_prob < MINIMUM_DRAW_PROBABILITY:
                draw_prob = MINIMUM_DRAW_PROBABILITY
                home_win_prob = (100 - draw_prob) * (home_win_prob / (home_win_prob + away_win_prob))
                away_win_prob = 100 - home_win_prob - draw_prob
    else:
        home_win_prob = DEFAULT_HOME_WIN_PROB
        draw_prob = DEFAULT_DRAW_PROB
        away_win_prob = DEFAULT_AWAY_WIN_PROB

    results = {"Home Win": 0, "Draw": 0, "Away Win": 0}
    scorelines = {}
    total_goals = 0
    btts_count = 0
    over_2_5_count = 0

    print("\n🔄 Simulating matches... Please wait...\n")

    for i in range(n_simulations):
        roll = random.randint(1, 100)

        if roll <= home_win_prob:
            outcome = "Home Win"
        elif roll <= home_win_prob + draw_prob:
            outcome = "Draw"
        else:
            outcome = "Away Win"

        results[outcome] += 1

        # Simulate goals
        home_goals = max(0, int(random.gauss(1.5, 1)))  # Home team scores: average 1.5 goals
        away_goals = max(0, int(random.gauss(1.2, 1)))  # Away team scores: average 1.2 goals

        scoreline = f"{home_goals}-{away_goals}"
        scorelines[scoreline] = scorelines.get(scoreline, 0) + 1

        # Track total goals
        total_goals += home_goals + away_goals

        # BTTS (both teams scored)
        if home_goals > 0 and away_goals > 0:
            btts_count += 1

        # Over 2.5 goals
        if home_goals + away_goals > 2:
            over_2_5_count += 1

        if (i + 1) % (n_simulations // 10) == 0:
            print("█", end="", flush=True)
        time.sleep(0.001)

    print("\n✅ Simulation complete!\n")

    # Calculate percentages
    over_2_5_percentage = over_2_5_count / n_simulations * 100
    btts_percentage = btts_count / n_simulations * 100
    average_goals = total_goals / n_simulations

    # Find most common scorelines
    sorted_scorelines = sorted(scorelines.items(), key=lambda x: x[1], reverse=True)
    top_scorelines = sorted_scorelines[:3]

    # Calculate confidence (how dominant is one result?)
    highest_result_count = max(results.values())
    confidence_score = (highest_result_count / n_simulations) * 100

    return {
        "results": results,
        "top_scorelines": top_scorelines,
        "average_goals": average_goals,
        "btts_percentage": btts_percentage,
        "over_2_5_percentage": over_2_5_percentage,
        "confidence_score": confidence_score
    }