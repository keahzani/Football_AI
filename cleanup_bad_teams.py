"""
Remove incorrectly-tagged non-league matches from Premier League data
"""
import sqlite3

conn = sqlite3.connect('data/football.db')
cursor = conn.cursor()

# These are the National League teams that got mixed into Premier League
bad_teams = [
    'Aldershot', 'Altrincham', 'Barrow', 'Boreham Wood', 'Boston Utd',
    'Carlisle', 'Eastleigh', 'Forest Green', 'Fylde', 'Gateshead',
    'Halifax', 'Harrogate', 'Hartlepool', 'Hornchurch', 'Kidderminster',
    'Scunthorpe', 'Solihull', 'Southend', 'Sutton', 'Tamworth',
    'Wealdstone', 'Woking', 'Worthing', 'Yeovil'
]

print("=" * 60)
print("CLEANUP: Removing non-league teams from Premier League")
print("=" * 60)

# Find matches involving these teams in Premier League
placeholders = ','.join('?' * len(bad_teams))
find_query = f"""
    SELECT m.match_id, ht.team_name, at.team_name, m.season
    FROM matches m
    JOIN teams ht ON m.home_team_id = ht.team_id
    JOIN teams at ON m.away_team_id = at.team_id
    JOIN leagues l ON m.league_id = l.league_id
    WHERE l.league_name = 'Premier League'
    AND (ht.team_name IN ({placeholders}) OR at.team_name IN ({placeholders}))
"""

cursor.execute(find_query, bad_teams + bad_teams)
bad_matches = cursor.fetchall()

print(f"\nFound {len(bad_matches)} matches to remove:")
for m in bad_matches:
    print(f"  Match ID {m[0]}: {m[1]} vs {m[2]} ({m[3]})")

if bad_matches:
    confirm = input(f"\nDelete these {len(bad_matches)} matches? (y/n): ")
    if confirm.lower() == 'y':
        match_ids = [m[0] for m in bad_matches]
        placeholders_ids = ','.join('?' * len(match_ids))
        
        cursor.execute(f"DELETE FROM matches WHERE match_id IN ({placeholders_ids})", match_ids)
        conn.commit()
        print(f"\n✅ Deleted {cursor.rowcount} bad matches!")
        
        # Now check for orphaned teams (teams with no matches left)
        cursor.execute("""
            SELECT t.team_id, t.team_name 
            FROM teams t
            LEFT JOIN matches m ON (t.team_id = m.home_team_id OR t.team_id = m.away_team_id)
            WHERE m.match_id IS NULL
            AND t.team_name IN ({})
        """.format(placeholders), bad_teams)
        
        orphaned = cursor.fetchall()
        if orphaned:
            print(f"\nFound {len(orphaned)} orphaned team records:")
            for t in orphaned:
                print(f"  {t[1]}")
            
            cleanup_teams = input("\nRemove these orphaned team records too? (y/n): ")
            if cleanup_teams.lower() == 'y':
                orphan_ids = [t[0] for t in orphaned]
                orphan_placeholders = ','.join('?' * len(orphan_ids))
                cursor.execute(f"DELETE FROM teams WHERE team_id IN ({orphan_placeholders})", orphan_ids)
                conn.commit()
                print(f"✅ Removed {cursor.rowcount} orphaned teams!")
    else:
        print("Cancelled - no changes made.")
else:
    print("\n✅ No bad matches found!")

# Verify the fix
print("\n" + "=" * 60)
print("VERIFICATION")
print("=" * 60)
cursor.execute("""
    SELECT COUNT(DISTINCT t.team_name)
    FROM matches m
    JOIN teams t ON (m.home_team_id = t.team_id OR m.away_team_id = t.team_id)
    JOIN leagues l ON m.league_id = l.league_id
    WHERE l.league_name = 'Premier League' AND m.season = '2526-2527'
""")
team_count = cursor.fetchone()[0]
print(f"Premier League 2526-2527 now has: {team_count} teams")
print("(Should be 20)")

conn.close()