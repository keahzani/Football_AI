"""
Check all leagues/seasons for team count anomalies
"""
import sqlite3

conn = sqlite3.connect('data/football.db')
cursor = conn.cursor()

cursor.execute("SELECT DISTINCT league_name FROM leagues")
leagues = [row[0] for row in cursor.fetchall()]

print("=" * 70)
print("TEAM COUNT CHECK - ALL LEAGUES, CURRENT SEASON")
print("=" * 70)

for league in leagues:
    cursor.execute("""
        SELECT DISTINCT m.season FROM matches m
        JOIN leagues l ON m.league_id = l.league_id
        WHERE l.league_name = ?
        ORDER BY season DESC LIMIT 1
    """, (league,))
    result = cursor.fetchone()
    if not result:
        continue
    season = result[0]
    
    cursor.execute("""
        SELECT COUNT(DISTINCT t.team_name)
        FROM matches m
        JOIN teams t ON (m.home_team_id = t.team_id OR m.away_team_id = t.team_id)
        JOIN leagues l ON m.league_id = l.league_id
        WHERE l.league_name = ? AND m.season = ?
    """, (league, season))
    team_count = cursor.fetchone()[0]
    
    flag = "⚠️ CHECK THIS" if team_count > 24 else "✅"
    print(f"{league:25s} | {season:12s} | {team_count:3d} teams | {flag}")

conn.close()