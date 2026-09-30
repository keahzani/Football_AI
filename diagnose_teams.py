"""
Diagnose which teams have too few matches (likely wrong league data)
"""
import sqlite3

conn = sqlite3.connect('data/football.db')
cursor = conn.cursor()

# First, let's see what leagues and seasons actually exist
print("=" * 60)
print("AVAILABLE LEAGUES AND SEASONS")
print("=" * 60)
cursor.execute("""
    SELECT l.league_name, m.season, COUNT(*) as matches
    FROM matches m
    JOIN leagues l ON m.league_id = l.league_id
    GROUP BY l.league_name, m.season
    ORDER BY l.league_name, m.season DESC
""")
for row in cursor.fetchall():
    print(row)

print()
print("=" * 60)
print("TEAMS WITH LOW MATCH COUNT (Premier League, current season)")
print("=" * 60)

# Get the most recent season for Premier League
cursor.execute("""
    SELECT DISTINCT season FROM matches m
    JOIN leagues l ON m.league_id = l.league_id
    WHERE l.league_name = 'Premier League'
    ORDER BY season DESC LIMIT 1
""")
current_season = cursor.fetchone()[0]
print(f"Current season detected: {current_season}")
print()

query = """
SELECT t.team_name, COUNT(*) as played
FROM matches m
JOIN teams t ON (m.home_team_id = t.team_id OR m.away_team_id = t.team_id)
JOIN leagues l ON m.league_id = l.league_id
WHERE l.league_name = ? AND m.season = ?
GROUP BY t.team_name
ORDER BY played ASC
"""
cursor.execute(query, ('Premier League', current_season))
results = cursor.fetchall()

print(f"Total teams found: {len(results)}")
print()
print("Lowest match counts (likely bad data):")
for row in results[:25]:
    print(f"  {row[0]}: {row[1]} matches")

conn.close()