# football_data_connect.py

import requests

# Your Football-Data.org API key
API_KEY = "ccdd6ec0f17d4ae0931ebcbd097c9b28"

# Define headers required by Football-Data.org API for authentication
headers = {
    "X-Auth-Token": API_KEY
}

def get_upcoming_fixtures():
    """
    Fetch upcoming scheduled fixtures for the English Premier League (PL).
    Returns a list of matches with basic information (home team, away team, match date).
    """
    url = "https://api.football-data.org/v4/competitions/PL/matches?status=SCHEDULED"  # Endpoint for scheduled EPL matches
    response = requests.get(url, headers=headers)

    data = response.json()
    fixtures = []

    # Extract relevant data for each fixture
    print("API response:", data)
    for match in data['matches']:
        fixtures.append({
            "match_id": match['id'],
            "home_team": match['homeTeam']['name'],
            "away_team": match['awayTeam']['name'],
            "date": match['utcDate'][:10]  # Only take yyyy-mm-dd part
        })

    return fixtures

def get_premier_league_standings():
    """
    Fetch the current Premier League standings.
    Returns a dictionary mapping team names to their position and points.
    """
    url = "https://api.football-data.org/v4/competitions/PL/standings"  # Endpoint for EPL standings
    response = requests.get(url, headers=headers)

    data = response.json()
    standings = {}

    # Build a dictionary with team names as keys and their position/points as values
    for team in data['standings'][0]['table']:
        standings[team['team']['name']] = {
            "position": team['position'],
            "points": team['points']
        }

    return standings