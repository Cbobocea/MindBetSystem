# esports_simulation.py
import math
import random


def get_team_strength(team_name, game_id, team_id=None):
    """
    Calculate the relative strength of a team based on available data.

    Args:
        team_name (str): Name of the team
        game_id (str): ID of the game
        team_id (int): Optional team ID for API lookups

    Returns:
        float: Team strength score between 0.1 and 1.0
    """
    from esports_data_connect import calculate_team_strength

    # If we have a team ID, use real data
    if team_id:
        return calculate_team_strength(game_id, team_name, team_id)

    # Fallback to pseudo-random
    return calculate_team_strength(game_id, team_name)


def simulate_esports_match(match_data, game_id, n_simulations=1000):
    """
    Main function to simulate an eSports match based on the game type.

    Args:
        match_data (dict): Match information including teams and team IDs
        game_id (str): ID of the game (csgo, lol, dota2, valorant)
        n_simulations (int): Number of simulations to run

    Returns:
        dict: Simulation results
    """
    home_team = match_data["home_team"]
    away_team = match_data["away_team"]
    home_team_id = match_data.get("home_team_id")
    away_team_id = match_data.get("away_team_id")
    best_of = match_data.get("best_of", 3)  # Default to best of 3

    if game_id == "csgo":
        return simulate_csgo_match(
            home_team, away_team, best_of, n_simulations,
            home_team_id=home_team_id, away_team_id=away_team_id
        )
    elif game_id == "lol":
        return simulate_lol_match(
            home_team, away_team, best_of, n_simulations,
            home_team_id=home_team_id, away_team_id=away_team_id
        )
    # ... other game types
    else:
        # Use generic simulation for other games
        return simulate_match_generic(
            home_team, away_team, best_of, n_simulations,
            home_team_id=home_team_id, away_team_id=away_team_id
        )


def simulate_csgo_match(home_team, away_team, best_of=3, n_simulations=1000,
                        home_team_id=None, away_team_id=None):
    """
    Simulate a CS:GO match with map picks and rounds.

    Args:
        home_team (str): Name of home team
        away_team (str): Name of away team
        best_of (int): Number of maps in the series
        n_simulations (int): Number of simulations to run
        home_team_id (int): Optional ID for API lookups
        away_team_id (int): Optional ID for API lookups

    Returns:
        dict: Simulation results with CS:GO specific stats
    """
    from esports_data_connect import calculate_h2h_advantage

    # Get team strengths based on recent performance
    home_strength = get_team_strength(home_team, "csgo", home_team_id)
    away_strength = get_team_strength(away_team, "csgo", away_team_id)

    # Apply head-to-head advantage if we have team IDs
    h2h_factor = 1.0
    if home_team_id and away_team_id:
        h2h_factor = calculate_h2h_advantage("csgo", home_team_id, away_team_id)

    # Apply the h2h factor to home strength
    home_strength *= h2h_factor

    # CS:GO maps
    cs_maps = ["Dust II", "Mirage", "Inferno", "Nuke", "Overpass", "Ancient", "Vertigo"]

    # Track simulation results
    results = {"home_win": 0, "away_win": 0}
    map_stats = {map_name: {"home_win": 0, "away_win": 0} for map_name in cs_maps}
    round_stats = {"home": [], "away": []}

    # Additional tracking variables
    pistol_rounds = {"home_win": 0, "away_win": 0}
    overtime_matches = 0
    total_rounds_played = 0
    close_maps = 0  # Maps with score difference <= 3

    for _ in range(n_simulations):
        # Select maps for this series
        series_maps = random.sample(cs_maps, min(best_of, len(cs_maps)))

        home_maps_won = 0
        away_maps_won = 0
        maps_needed_to_win = (best_of // 2) + 1

        for map_name in series_maps:
            # Add randomness for this map
            map_home_strength = home_strength * random.uniform(0.9, 1.1)
            map_away_strength = away_strength * random.uniform(0.9, 1.1)

            # Simulate pistol rounds (slightly favor the team with higher strength)
            pistol_round_home_win_prob = map_home_strength / (map_home_strength + map_away_strength)

            # First half pistol
            if random.random() < pistol_round_home_win_prob:
                pistol_rounds["home_win"] += 1
            else:
                pistol_rounds["away_win"] += 1

            # Second half pistol
            if random.random() < pistol_round_home_win_prob:
                pistol_rounds["home_win"] += 1
            else:
                pistol_rounds["away_win"] += 1

            # Determine map winner based on strength
            home_rounds = 0
            away_rounds = 0

            # Check if the map goes to overtime (15-15)
            if random.random() < 0.12:  # ~12% chance of overtime
                overtime_matches += 1
                home_rounds = 15
                away_rounds = 15

                # Simulate overtime
                ot_rounds = random.randint(1, 6)  # Rounds needed in overtime
                if random.random() < map_home_strength / (map_home_strength + map_away_strength):
                    home_rounds = 19  # 15 + 4 (minimum for OT win)
                    away_rounds = 15 + ot_rounds
                    home_maps_won += 1
                    map_stats[map_name]["home_win"] += 1
                else:
                    away_rounds = 19
                    home_rounds = 15 + ot_rounds
                    away_maps_won += 1
                    map_stats[map_name]["away_win"] += 1
            else:
                # Regular map outcome
                if random.random() < map_home_strength / (map_home_strength + map_away_strength):
                    home_maps_won += 1
                    map_stats[map_name]["home_win"] += 1

                    # Simulate rounds (between 16-0 and 16-14)
                    away_rounds = random.randint(0, 14)
                    home_rounds = 16
                else:
                    away_maps_won += 1
                    map_stats[map_name]["away_win"] += 1

                    # Simulate rounds
                    home_rounds = random.randint(0, 14)
                    away_rounds = 16

            round_stats["home"].append(home_rounds)
            round_stats["away"].append(away_rounds)

            # Count total rounds and check if it was a close map
            map_total_rounds = home_rounds + away_rounds
            total_rounds_played += map_total_rounds

            if abs(home_rounds - away_rounds) <= 3:
                close_maps += 1

            # Stop if one team has won enough maps
            if home_maps_won >= maps_needed_to_win:
                results["home_win"] += 1
                break
            elif away_maps_won >= maps_needed_to_win:
                results["away_win"] += 1
                break


    # Calculate probabilities
    home_win_probability = results["home_win"] / n_simulations
    away_win_probability = results["away_win"] / n_simulations

    # Calculate map win rates
    map_win_rates = {}
    for map_name in cs_maps:
        total_map_games = map_stats[map_name]["home_win"] + map_stats[map_name]["away_win"]
        if total_map_games > 0:
            map_win_rates[map_name] = {
                "home": map_stats[map_name]["home_win"] / total_map_games,
                "away": map_stats[map_name]["away_win"] / total_map_games
            }

    # Calculate average rounds
    avg_home_rounds = sum(round_stats["home"]) / len(round_stats["home"]) if round_stats["home"] else 0
    avg_away_rounds = sum(round_stats["away"]) / len(round_stats["away"]) if round_stats["away"] else 0

    # Calculate confidence score
    confidence_score = max(home_win_probability, away_win_probability) * 100

    # Calculate new statistics
    avg_rounds_per_map = total_rounds_played / (
        sum(map_stats[m]["home_win"] + map_stats[m]["away_win"] for m in cs_maps))
    pistol_round_home_win_rate = pistol_rounds["home_win"] / (pistol_rounds["home_win"] + pistol_rounds["away_win"])
    overtime_percentage = (overtime_matches / n_simulations) * 100
    close_maps_percentage = (close_maps / (
        sum(map_stats[m]["home_win"] + map_stats[m]["away_win"] for m in cs_maps))) * 100

    # Most favorable maps for each team
    home_best_maps = sorted([(m, map_win_rates[m]["home"]) for m in map_win_rates], key=lambda x: x[1], reverse=True)[
                     :3]
    away_best_maps = sorted([(m, map_win_rates[m]["away"]) for m in map_win_rates], key=lambda x: x[1], reverse=True)[
                     :3]

    # Series score distribution (like 2-0, 2-1, etc.)
    score_distribution = {}
    for home_score in range(maps_needed_to_win + 1):
        for away_score in range(maps_needed_to_win + 1):
            if home_score == maps_needed_to_win or away_score == maps_needed_to_win:
                score_key = f"{home_score}-{away_score}"
                score_distribution[score_key] = 0  # Will be populated in a second pass

    # Need a second simulation to track score distribution
    for _ in range(min(1000, n_simulations)):  # Limit to 1000 to avoid too much computation
        home_maps = 0
        away_maps = 0
        maps_needed_to_win = (best_of // 2) + 1

        for _ in range(best_of):
            # Simplified map simulation
            if random.random() < home_strength / (home_strength + away_strength):
                home_maps += 1
            else:
                away_maps += 1

            if home_maps >= maps_needed_to_win or away_maps >= maps_needed_to_win:
                score_key = f"{home_maps}-{away_maps}"
                if score_key in score_distribution:
                    score_distribution[score_key] += 1
                break

    # Normalize score distribution
    total_scores = sum(score_distribution.values())
    if total_scores > 0:
        for key in score_distribution:
            score_distribution[key] = score_distribution[key] / total_scores

    return {
        "home_team": home_team,
        "away_team": away_team,
        "best_of": best_of,
        "results": {
            "home_win": home_win_probability,
            "away_win": away_win_probability
        },
        "map_stats": map_win_rates,
        "round_stats": {
            "avg_home_rounds": round(avg_home_rounds, 1),
            "avg_away_rounds": round(avg_away_rounds, 1)
        },
        "confidence_score": confidence_score,
        "simulations": n_simulations,

        "pistol_rounds": {
            "home_win_rate": round(pistol_round_home_win_rate * 100, 1),
            "away_win_rate": round((1 - pistol_round_home_win_rate) * 100, 1)
        },
        "map_analysis": {
            "avg_rounds_per_map": round(avg_rounds_per_map, 1),
            "overtime_percentage": round(overtime_percentage, 1),
            "close_maps_percentage": round(close_maps_percentage, 1),
            "home_best_maps": [{"name": m[0], "win_rate": round(m[1] * 100, 1)} for m in home_best_maps],
            "away_best_maps": [{"name": m[0], "win_rate": round(m[1] * 100, 1)} for m in away_best_maps]
        },
        "score_distribution": {k: round(v * 100, 1) for k, v in score_distribution.items()},
        "expected_total_maps": round(sum(sum(stats.values()) for map_name, stats in map_stats.items()), 1)
    }



def simulate_lol_match(home_team, away_team, best_of=3, n_simulations=1000,
                       home_team_id=None, away_team_id=None):
    """
    League of Legends specific simulation.

    Args:
        home_team (str): Name of home team
        away_team (str): Name of away team
        best_of (int): Number of games in the series
        n_simulations (int): Number of simulations to run
        home_team_id (int): Optional ID for API lookups
        away_team_id (int): Optional ID for API lookups

    Returns:
        dict: Simulation results with LoL specific stats
    """
    # Get team strengths
    home_strength = get_team_strength(home_team, "lol", home_team_id)
    away_strength = get_team_strength(away_team, "lol", away_team_id)

    results = {"home_win": 0, "away_win": 0}
    game_lengths = []
    kill_distributions = {"home": [], "away": []}

    # Additional tracking variables
    first_bloods = {"home": 0, "away": 0}
    dragons_per_game = {"home": [], "away": []}
    barons_per_game = {"home": [], "away": []}
    game_duration_distribution = {"under25": 0, "25to35": 0, "over35": 0}
    first_drakes = {"home": 0, "away": 0}

    for _ in range(n_simulations):
        home_games_won = 0
        away_games_won = 0
        games_needed_to_win = (best_of // 2) + 1

        for _ in range(best_of):
            # For each game in the series
            game_home_strength = home_strength * random.uniform(0.95, 1.05)
            game_away_strength = away_strength * random.uniform(0.95, 1.05)

            # Simulate first blood (slightly favor stronger team)
            first_blood_home_prob = game_home_strength / (game_home_strength + game_away_strength)
            if random.random() < first_blood_home_prob:
                first_bloods["home"] += 1
            else:
                first_bloods["away"] += 1

            # Determine game winner based on team strength
            game_length = random.randint(20, 45)
            game_lengths.append(game_length)

            if random.random() < game_home_strength / (game_home_strength + game_away_strength):
                home_games_won += 1

                # Simulate kill counts
                home_kills = int(random.normalvariate(18, 5))
                away_kills = int(random.normalvariate(12, 4))
                kill_distributions["home"].append(home_kills)
                kill_distributions["away"].append(away_kills)

                # Simulate dragon control for winning team
                home_dragons = int(random.normalvariate(3, 1))
                away_dragons = int(random.normalvariate(1.5, 1))
            else:
                away_games_won += 1

                # Simulate kill counts
                home_kills = int(random.normalvariate(12, 4))
                away_kills = int(random.normalvariate(18, 5))
                kill_distributions["home"].append(home_kills)
                kill_distributions["away"].append(away_kills)

                # Simulate dragon control for winning team
                home_dragons = int(random.normalvariate(1.5, 1))
                away_dragons = int(random.normalvariate(3, 1))

            dragons_per_game["home"].append(max(0, home_dragons))
            dragons_per_game["away"].append(max(0, away_dragons))

            # Simulate first drake
            if random.random() < game_home_strength / (game_home_strength + game_away_strength):
                first_drakes["home"] += 1
            else:
                first_drakes["away"] += 1

            # Simulate baron control
            home_barons = int(random.normalvariate(
                1 if random.random() < game_home_strength / (game_home_strength + game_away_strength) else 0.3, 0.7))
            away_barons = int(random.normalvariate(
                1 if random.random() < game_away_strength / (game_home_strength + game_away_strength) else 0.3, 0.7))
            barons_per_game["home"].append(max(0, home_barons))
            barons_per_game["away"].append(max(0, away_barons))

            # Categorize game duration
            if game_length < 25:
                game_duration_distribution["under25"] += 1
            elif game_length < 35:
                game_duration_distribution["25to35"] += 1
            else:
                game_duration_distribution["over35"] += 1

            # Early termination if a team has won enough games
            if home_games_won >= games_needed_to_win:
                results["home_win"] += 1
                break
            elif away_games_won >= games_needed_to_win:
                results["away_win"] += 1
                break


    # Calculate statistics
    home_win_probability = results["home_win"] / n_simulations
    away_win_probability = results["away_win"] / n_simulations
    avg_game_length = sum(game_lengths) / len(game_lengths) if game_lengths else 0
    avg_home_kills = sum(kill_distributions["home"]) / len(kill_distributions["home"]) if kill_distributions[
        "home"] else 0
    avg_away_kills = sum(kill_distributions["away"]) / len(kill_distributions["away"]) if kill_distributions[
        "away"] else 0

    # Calculate confidence score
    confidence_score = max(home_win_probability, away_win_probability) * 100

    # Calculate new statistics
    total_games = len(game_lengths)

    # First blood percentage
    first_blood_home_rate = first_bloods["home"] / total_games if total_games > 0 else 0.5

    # Average dragons and barons
    avg_home_dragons = sum(dragons_per_game["home"]) / len(dragons_per_game["home"]) if dragons_per_game["home"] else 0
    avg_away_dragons = sum(dragons_per_game["away"]) / len(dragons_per_game["away"]) if dragons_per_game["away"] else 0
    avg_home_barons = sum(barons_per_game["home"]) / len(barons_per_game["home"]) if barons_per_game["home"] else 0
    avg_away_barons = sum(barons_per_game["away"]) / len(barons_per_game["away"]) if barons_per_game["away"] else 0

    # First drake percentage
    first_drake_home_rate = first_drakes["home"] / total_games if total_games > 0 else 0.5

    # Game duration distribution
    for key in game_duration_distribution:
        game_duration_distribution[key] = game_duration_distribution[key] / total_games if total_games > 0 else 0

    # Series score distribution (like 2-0, 2-1, etc.)
    score_distribution = {}
    for home_score in range(games_needed_to_win + 1):
        for away_score in range(games_needed_to_win + 1):
            if home_score == games_needed_to_win or away_score == games_needed_to_win:
                score_key = f"{home_score}-{away_score}"
                score_distribution[score_key] = 0

    # Second pass for score distribution
    for _ in range(min(1000, n_simulations)):
        home_games = 0
        away_games = 0

        for _ in range(best_of):
            if random.random() < home_strength / (home_strength + away_strength):
                home_games += 1
            else:
                away_games += 1

            if home_games >= games_needed_to_win or away_games >= games_needed_to_win:
                score_key = f"{home_games}-{away_games}"
                if score_key in score_distribution:
                    score_distribution[score_key] += 1
                break

    # Normalize score distribution
    total_scores = sum(score_distribution.values())
    if total_scores > 0:
        for key in score_distribution:
            score_distribution[key] = score_distribution[key] / total_scores

    return {
        "home_team": home_team,
        "away_team": away_team,
        "best_of": best_of,
        "results": {
            "home_win": home_win_probability,
            "away_win": away_win_probability
        },
        "confidence_score": confidence_score,
    "simulations": n_simulations,
    "game_stats": {
        "avg_game_length": round(avg_game_length, 1),
        "avg_home_kills": round(avg_home_kills, 1),
        "avg_away_kills": round(avg_away_kills, 1),
        "avg_home_dragons": round(avg_home_dragons, 1),
        "avg_away_dragons": round(avg_away_dragons, 1),
        "avg_home_barons": round(avg_home_barons, 1),
        "avg_away_barons": round(avg_away_barons, 1)
    },
        "early_game": {
            "first_blood_home": round(first_blood_home_rate * 100, 1),
            "first_blood_away": round((1 - first_blood_home_rate) * 100, 1),
            "first_drake_home": round(first_drake_home_rate * 100, 1),
            "first_drake_away": round((1 - first_drake_home_rate) * 100, 1)
        },
        "game_duration": {
            "under_25_min": round(game_duration_distribution["under25"] * 100, 1),
            "25_to_35_min": round(game_duration_distribution["25to35"] * 100, 1),
            "over_35_min": round(game_duration_distribution["over35"] * 100, 1),
        },
        "score_distribution": {k: round(v * 100, 1) for k, v in score_distribution.items()}
    }



def simulate_match_generic(home_team, away_team, best_of=3, n_simulations=1000,
                           home_team_id=None, away_team_id=None):
    """
    Generic match simulation for any eSports game.

    Args:
        home_team (str): Name of home team
        away_team (str): Name of away team
        best_of (int): Number of games in the series
        n_simulations (int): Number of simulations to run
        home_team_id (int): Optional ID for API lookups
        away_team_id (int): Optional ID for API lookups

    Returns:
        dict: Simulation results
    """
    # Get team strengths (these will be pseudo-random but consistent for the same team)
    home_strength = get_team_strength(home_team, "generic", home_team_id)
    away_strength = get_team_strength(away_team, "generic", away_team_id)

    # Add a small home advantage
    home_strength *= 1.05

    # Track additional data
    game_scores = []
    home_blowouts = 0  # Games with very dominant home team performance
    away_blowouts = 0  # Games with very dominant away team performance
    close_games = 0  # Games decided by a small margin

    results = {"home_win": 0, "away_win": 0}

    for _ in range(n_simulations):
        home_wins = 0
        away_wins = 0
        maps_needed = (best_of // 2) + 1

        # Simulate individual game scores
        series_scores = []

        for _ in range(best_of):
            # Add a small random factor for each game
            game_home_strength = home_strength * random.uniform(0.9, 1.1)
            game_away_strength = away_strength * random.uniform(0.9, 1.1)

            # Simulate a score for this game (could be points, goals, etc.)
            home_score = int(random.normalvariate(25 * game_home_strength, 5))
            away_score = int(random.normalvariate(25 * game_away_strength, 5))

            # Ensure positive scores
            home_score = max(1, home_score)
            away_score = max(1, away_score)

            series_scores.append((home_score, away_score))

            # Check if the game was a blowout or close
            score_diff = abs(home_score - away_score)
            if score_diff > 15:  # Arbitrary threshold for a blowout
                if home_score > away_score:
                    home_blowouts += 1
                else:
                    away_blowouts += 1
            elif score_diff < 5:  # Arbitrary threshold for a close game
                close_games += 1

            # Determine winner based on relative strengths (can also use the scores to determine the winner)
            if home_score > away_score:
                home_wins += 1
            else:
                away_wins += 1

            # Stop if one team has won enough games
            if home_wins >= maps_needed:
                results["home_win"] += 1
                break
            elif away_wins >= maps_needed:
                results["away_win"] += 1
                break

        game_scores.append(series_scores)

    # Calculate probabilities
    home_win_probability = results["home_win"] / n_simulations
    away_win_probability = results["away_win"] / n_simulations

    # Calculate confidence score
    confidence_score = max(home_win_probability, away_win_probability) * 100

    # Calculate average scores and score difference
    all_home_scores = [score[0] for series in game_scores for score in series]
    all_away_scores = [score[1] for series in game_scores for score in series]

    avg_home_score = sum(all_home_scores) / len(all_home_scores) if all_home_scores else 0
    avg_away_score = sum(all_away_scores) / len(all_away_scores) if all_away_scores else 0
    avg_score_diff = sum(abs(h - a) for h, a in zip(all_home_scores, all_away_scores)) / len(
        all_home_scores) if all_home_scores else 0

    # Calculate blowout and close game percentages
    total_games = len(all_home_scores)
    blowout_percentage = ((home_blowouts + away_blowouts) / total_games) * 100 if total_games > 0 else 0
    close_game_percentage = (close_games / total_games) * 100 if total_games > 0 else 0

    # Series score distribution
    score_distribution = {}
    for home_score in range(maps_needed + 1):
        for away_score in range(maps_needed + 1):
            if home_score == maps_needed or away_score == maps_needed:
                score_key = f"{home_score}-{away_score}"
                score_distribution[score_key] = 0

    # Second pass for score distribution
    for _ in range(min(1000, n_simulations)):
        home_wins = 0
        away_wins = 0

        for _ in range(best_of):
            if random.random() < home_strength / (home_strength + away_strength):
                home_wins += 1
            else:
                away_wins += 1

            if home_wins >= maps_needed or away_wins >= maps_needed:
                score_key = f"{home_wins}-{away_wins}"
                if score_key in score_distribution:
                    score_distribution[score_key] += 1
                break

    # Normalize score distribution
    total_scores = sum(score_distribution.values())
    for key in score_distribution:
        if total_scores > 0:
            score_distribution[key] = score_distribution[key] / total_scores

    return {
        "home_team": home_team,
        "away_team": away_team,
        "best_of": best_of,
        "results": {
            "home_win": home_win_probability,
            "away_win": away_win_probability
        },
        "confidence_score": confidence_score,
        "simulations": n_simulations,
        "game_stats": {
            "avg_home_score": round(avg_home_score, 1),
            "avg_away_score": round(avg_away_score, 1),
            "avg_score_diff": round(avg_score_diff, 1)
        },
        "game_flow": {
            "blowout_percentage": round(blowout_percentage, 1),
            "close_game_percentage": round(close_game_percentage, 1),
            "home_dominance": round((home_blowouts / total_games) * 100, 1) if total_games > 0 else 0,
            "away_dominance": round((away_blowouts / total_games) * 100, 1) if total_games > 0 else 0
        },
        "score_distribution": {k: round(v * 100, 1) for k, v in score_distribution.items()}
    }



def simulate_match(match_data):
    """
    Bridge function to match the function name expected by app.py.

    Args:
        match_data (dict): Match information including teams

    Returns:
        dict: Simulation results
    """
    game_id = match_data.get("game_id", "csgo")
    return simulate_esports_match(match_data, game_id)