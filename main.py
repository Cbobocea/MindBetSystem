from football_data_connect import get_upcoming_fixtures, get_premier_league_standings
from simulate_from_dataorg import simulate_match_full
import time

def main():
    standings = get_premier_league_standings()
    fixtures = get_upcoming_fixtures()

    print("\n📅 Upcoming Matches:")
    for idx, match in enumerate(fixtures):
        print(f"[{idx}] {match['home_team']} vs {match['away_team']} on {match['date']}")

    try:
        choice = int(input("\nSelect a match number: "))
        selected_match = fixtures[choice]
    except (ValueError, IndexError):
        print("⚠️ Invalid choice. Exiting.")
        return

    simulation = simulate_match_full(selected_match, standings)

    print("\n🎯 Simulation Results over 1000 matches:")
    for result, count in simulation["results"].items():
        print(f"- {result}: {count} ({count/10:.1f}%)")

    print("\n🏆 Most Common Scorelines:")
    for scoreline, freq in simulation["top_scorelines"]:
        print(f"- {scoreline}: {freq} times")

    print(f"\n📈 Average Goals Per Match: {simulation['average_goals']:.2f}")
    print(f"⚽ Both Teams Scored (BTTS): {simulation['btts_percentage']:.1f}%")
    print(f"📊 Over 2.5 Goals: {simulation['over_2_5_percentage']:.1f}%")
    print(f"💬 Mindbet Confidence Score: {simulation['confidence_score']:.1f}%")

    # === Suggested Bets Section ===

    print("\n🧠 Suggested Bets Based on Simulation:")

    # Suggest BTTS
    if simulation["btts_percentage"] > 60:
        print("- ✅ Both Teams To Score: YES")
    elif simulation["btts_percentage"] < 40:
        print("- ✅ Both Teams To Score: NO")

    # Suggest Over/Under 2.5 Goals
    if simulation["over_2_5_percentage"] > 55:
        print("- ✅ Over 2.5 Goals")
    elif simulation["over_2_5_percentage"] < 40:
        print("- ✅ Under 2.5 Goals")

    # Suggest based on Win/Draw/Away if confidence is strong
    if simulation["confidence_score"] > 70:
        # Find dominant outcome
        dominant_result = max(simulation["results"], key=simulation["results"].get)
        print(f"- ✅ Bet on {dominant_result}")
    else:
        print("- ⚡ No strong winner predicted (match balanced)")

if __name__ == "__main__":
    main()