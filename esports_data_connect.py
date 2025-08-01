# esports_data_connect.py
import requests
import os
from datetime import datetime, timedelta
import time
# esports_data_connect.py
import requests
import os
from datetime import datetime, timedelta
import time
import random  # Make sure this is included

# PandaScore API key
API_KEY = "casG8zCts6dfij_rqAvNIGsytRK2WfsVN58fT8tFIGhS8nmBWhQ"

# Define headers for API authentication
headers = {
    "Authorization": f"Bearer {API_KEY}"
}

# API base URL
BASE_URL = "https://api.pandascore.co"


# In esports_data_connect.py
def get_team_recent_results(game_id, team_id, limit=10):
    """
    Get recent match results for a specific team.

    Args:
        game_id (str): ID of the game
        team_id (int): ID of the team
        limit (int): Maximum number of matches to return

    Returns:
        list: Recent match results
    """
    url = f"{BASE_URL}/{game_id}/matches/past?filter[opponent_id]={team_id}&sort=-begin_at&per_page={limit}"

    try:
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"API Error: {response.status_code}")
            return []

        return response.json()
    except Exception as e:
        print(f"Failed to fetch recent results: {e}")
        return []


def calculate_team_strength(game_id, team_name, team_id=None):
    """
    Calculate team strength based on recent performance.

    Args:
        game_id (str): ID of the game
        team_name (str): Name of the team
        team_id (int): Optional team ID

    Returns:
        float: Team strength between 0.35 and 0.9
    """
    # Default to pseudo-random if no team_id
    if not team_id:
        return get_pseudo_random_strength(team_name)

    # Get recent matches
    recent_matches = get_team_recent_results(game_id, team_id, limit=10)

    if not recent_matches:
        return get_pseudo_random_strength(team_name)

    # Calculate win rate
    wins = 0
    total = len(recent_matches)

    for match in recent_matches:
        if match.get('winner_id') == team_id:
            wins += 1

    win_rate = wins / total if total > 0 else 0.5

    # Scale win rate to strength (0.4-0.85 range)
    base_strength = 0.4 + (win_rate * 0.45)

    # Add small random variation
    variation = random.uniform(-0.05, 0.05)

    return max(0.35, min(0.9, base_strength + variation))


def get_pseudo_random_strength(team_name):
    """
    Fallback to pseudo-random strength based on team name.

    Args:
        team_name (str): Name of the team

    Returns:
        float: Team strength between 0.35 and 0.9
    """
    # Use team name as seed for consistency
    seed = sum(ord(c) for c in team_name)
    random.seed(seed)

    # Generate base strength
    base_strength = 0.4 + (random.random() * 0.45)

    # Reset random seed
    random.seed()

    # Add variation
    variation = random.uniform(-0.05, 0.05)

    return max(0.35, min(0.9, base_strength + variation))


# In esports_data_connect.py
def get_head_to_head(game_id, team1_id, team2_id, limit=5):
    """
    Get head-to-head match history between two teams.

    Args:
        game_id (str): ID of the game
        team1_id (int): ID of the first team
        team2_id (int): ID of the second team
        limit (int): Maximum number of matches to return

    Returns:
        list: Head-to-head match history
    """
    url = f"{BASE_URL}/{game_id}/matches/past?filter[opponent_id]={team1_id}&filter[opponent_id]={team2_id}&sort=-begin_at&per_page={limit}"

    try:
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"API Error: {response.status_code}")
            return []

        return response.json()
    except Exception as e:
        print(f"Failed to fetch head-to-head: {e}")
        return []


def calculate_h2h_advantage(game_id, team1_id, team2_id):
    """
    Calculate head-to-head advantage between two teams.

    Args:
        game_id (str): ID of the game
        team1_id (int): ID of the first team
        team2_id (int): ID of the second team

    Returns:
        float: Advantage factor for team1 (1.0 means neutral)
    """
    h2h_matches = get_head_to_head(game_id, team1_id, team2_id)

    if not h2h_matches:
        return 1.0  # Neutral

    team1_wins = 0
    total = len(h2h_matches)

    for match in h2h_matches:
        if match.get('winner_id') == team1_id:
            team1_wins += 1

    if total == 0:
        return 1.0

    win_rate = team1_wins / total

    # Scale to advantage factor (0.8-1.2)
    return 0.8 + (win_rate * 0.4)



def get_supported_games():
    """
    Returns a list of supported eSports games in the system.
    """
    return [
        {"id": "csgo", "name": "CS:GO", "full_name": "Counter-Strike: Global Offensive"},
        {"id": "lol", "name": "LoL", "full_name": "League of Legends"},
        {"id": "dota2", "name": "Dota 2", "full_name": "Dota 2"},
        {"id": "valorant", "name": "Valorant", "full_name": "Valorant"}
    ]


def get_upcoming_esports_matches(game_id="csgo", limit=10):
    """
    Fetch upcoming scheduled eSports matches for a specific game from PandaScore API.

    Args:
        game_id (str): ID of the game (csgo, lol, dota2, valorant)
        limit (int): Maximum number of matches to return

    Returns:
        A list of matches with basic information
    """
    url = f"{BASE_URL}/{game_id}/matches/upcoming?sort=begin_at&per_page={limit}"

    try:
        print(f"Fetching matches from: {url}")
        response = requests.get(url, headers=headers)

        # Check if response is successful
        if response.status_code != 200:
            print(f"API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return fallback_upcoming_matches(game_id, limit)

        data = response.json()
        matches = []

        for match in data:
            try:
                # Extract tournament data
                tournament_name = match.get('tournament', {}).get('name', 'Unknown Tournament')
                league_name = match.get('league', {}).get('name', 'Unknown League')

                # Extract team data safely
                opponents = match.get('opponents', [])
                home_team = "TBD"
                away_team = "TBD"
                home_team_id = None
                away_team_id = None

                if len(opponents) > 0 and 'opponent' in opponents[0]:
                    home_team = opponents[0]['opponent'].get('name', 'TBD')
                    home_team_id = opponents[0]['opponent'].get('id')

                if len(opponents) > 1 and 'opponent' in opponents[1]:
                    away_team = opponents[1]['opponent'].get('name', 'TBD')
                    away_team_id = opponents[1]['opponent'].get('id')

                # Format date and time
                begin_at = match.get('begin_at', '')
                date = begin_at[:10] if begin_at else datetime.now().strftime("%Y-%m-%d")
                time = begin_at[11:19] if len(begin_at) > 10 else "00:00:00"

                # Get match format
                best_of = match.get('number_of_games', 3)

                # Some games like CSGO have the match status
                status = match.get('status', 'not_started')

                matches.append({
                    "match_id": match.get('id', 0),
                    "home_team": home_team,
                    "away_team": away_team,
                    "home_team_id": home_team_id,
                    "away_team_id": away_team_id,
                    "date": date,
                    "time": time,
                    "best_of": best_of,
                    "tournament_name": f"{league_name}: {tournament_name}",
                    "status": status
                })
            except Exception as e:
                print(f"Error parsing match data: {e}")
                continue

        return matches

    except Exception as e:
        print(f"Failed to fetch upcoming matches: {e}")
        return fallback_upcoming_matches(game_id, limit)


def get_recent_results(game_id="csgo", limit=10):
    """
    Fetch recent completed matches for a specific game.

    Args:
        game_id (str): ID of the game
        limit (int): Maximum number of matches to return

    Returns:
        list: Recent match results
    """
    url = f"{BASE_URL}/{game_id}/matches/past?sort=-end_at&per_page={limit}"

    try:
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"API Error: {response.status_code}")
            return []

        data = response.json()
        results = []

        for match in data:
            try:
                # Extract team data
                opponents = match.get('opponents', [])
                home_team = "Unknown"
                away_team = "Unknown"

                if len(opponents) > 0 and 'opponent' in opponents[0]:
                    home_team = opponents[0]['opponent'].get('name', 'Unknown')

                if len(opponents) > 1 and 'opponent' in opponents[1]:
                    away_team = opponents[1]['opponent'].get('name', 'Unknown')

                # Get result data
                winner_id = match.get('winner_id')
                winner = "Draw"

                if winner_id and len(opponents) > 0:
                    if len(opponents) > 0 and 'opponent' in opponents[0] and opponents[0]['opponent'].get(
                            'id') == winner_id:
                        winner = home_team
                    elif len(opponents) > 1 and 'opponent' in opponents[1] and opponents[1]['opponent'].get(
                            'id') == winner_id:
                        winner = away_team

                # Format date
                end_at = match.get('end_at', '')
                date = end_at[:10] if end_at else datetime.now().strftime("%Y-%m-%d")

                # Get match score if available
                results_data = match.get('results', [])
                score_text = "Unknown Score"

                if len(results_data) >= 2:
                    score_text = f"{results_data[0].get('score', 0)} - {results_data[1].get('score', 0)}"

                results.append({
                    "match_id": match.get('id', 0),
                    "home_team": home_team,
                    "away_team": away_team,
                    "winner": winner,
                    "score": score_text,
                    "date": date,
                    "tournament_name": match.get('tournament', {}).get('name', 'Unknown Tournament')
                })
            except Exception as e:
                print(f"Error parsing result data: {e}")
                continue

        return results

    except Exception as e:
        print(f"Failed to fetch recent results: {e}")
        return []


def get_leagues_for_game(game_id="csgo", limit=10):
    """
    Get a list of active leagues for a game.

    Args:
        game_id (str): ID of the game
        limit (int): Maximum number of leagues to return

    Returns:
        list: Leagues for the game
    """
    url = f"{BASE_URL}/{game_id}/leagues?per_page={limit}"

    try:
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"API Error: {response.status_code}")
            return []

        return response.json()

    except Exception as e:
        print(f"Failed to fetch leagues: {e}")
        return []


def fallback_upcoming_matches(game_id="csgo", limit=10):
    """
    Generate fallback mock data when the API fails.
    """
    import random
    from datetime import datetime, timedelta

    # Teams by game
    teams = {
        "csgo": ["Natus Vincere", "Astralis", "Team Liquid", "FaZe Clan", "Vitality", "G2 Esports", "Fnatic", "NiP",
                 "Complexity", "ENCE"],
        "lol": ["T1", "Gen.G", "DRX", "G2 Esports", "Fnatic", "Team Liquid", "Cloud9", "DWG KIA", "JD Gaming",
                "Top Esports"],
        "dota2": ["Team Secret", "OG", "Team Liquid", "PSG.LGD", "Virtus.pro", "Evil Geniuses", "Nigma Galaxy",
                  "Alliance", "Tundra Esports", "Fnatic"],
        "valorant": ["Sentinels", "100 Thieves", "Team Liquid", "Fnatic", "Vision Strikers", "G2 Esports",
                     "KRÜ Esports", "NUTURN", "Version1", "Cloud9"]
    }

    tournaments = {
        "csgo": ["ESL Pro League", "BLAST Premier", "IEM Katowice", "DreamHack Masters", "ELEAGUE Major"],
        "lol": ["LEC", "LCS", "LCK", "LPL", "Mid-Season Invitational", "World Championship"],
        "dota2": ["The International", "ESL One", "DreamLeague", "The Manila Major", "MDL Chengdu Major"],
        "valorant": ["VCT Masters", "VCT Champions", "Red Bull Home Ground", "First Strike", "Challengers"]
    }

    matches = []

    # Get the teams for the requested game
    game_teams = teams.get(game_id, teams["csgo"])
    game_tournaments = tournaments.get(game_id, tournaments["csgo"])

    # Generate random matches
    for i in range(min(limit, 10)):  # Generate up to 10 matches
        # Pick two different teams
        home_team, away_team = random.sample(game_teams, 2)

        # Generate a future date (0-14 days in the future)
        future_date = datetime.now() + timedelta(days=random.randint(0, 14))
        date_str = future_date.strftime("%Y-%m-%d")
        time_str = f"{random.randint(10, 23)}:{random.choice(['00', '15', '30', '45'])}"

        best_of = random.choice([1, 3, 5])
        tournament = random.choice(game_tournaments)

        matches.append({
            "match_id": 1000 + i,
            "home_team": home_team,
            "away_team": away_team,
            "date": date_str,
            "time": time_str,
            "best_of": best_of,
            "tournament_name": tournament,
            "status": "not_started"
        })

    print("Using fallback data for upcoming matches")
    return matches