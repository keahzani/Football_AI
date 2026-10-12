"""
Diagnose La Liga team contamination
"""
import sqlite3

conn = sqlite3.connect('data/football.db')
cursor = conn.cursor()

print("=" * 60)
print("LA LIGA - Current Season Team Breakdown")
print("=" * 60)

cursor.execute("""
    SELECT DISTINCT season FROM matches m
    JOIN leagues l ON m.league_id = l.league_id
    WHERE l.league_name = 'La Liga'
    ORDER BY season DESC LIMIT 1
""")
current_season = cursor.fetchone()[0]
print(f"Current season: {current_season}\n")

query = """
SELECT t.team_name, COUNT(*) as played
FROM matches m
JOIN teams t ON (m.home_team_id = t.team_id OR m.away_team_id = t.team_id)
JOIN leagues l ON m.league_id = l.league_id
WHERE l.league_name = 'La Liga' AND m.season = ?
GROUP BY t.team_name
ORDER BY played ASC
"""
cursor.execute(query, (current_season,))
results = cursor.fetchall()

print(f"Total teams found: {len(results)}\n")
print("All teams sorted by match count (low to high):")
for row in results:
    print(f"  {row[0]}: {row[1]} matches")

conn.close()