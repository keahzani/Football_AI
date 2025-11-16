"""
Check and fix duplicate matches in database
FIXED VERSION - works without match_date column
"""
import sqlite3
from pathlib import Path

def check_duplicates():
    """Check for duplicate matches in database"""
    db_path = Path("data/football.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check for duplicate matches (same teams, season, score)
    query = """
    SELECT 
        l.league_name,
        m.season,
        ht.team_name as home_team,
        at.team_name as away_team,
        m.home_goals,
        m.away_goals,
        COUNT(*) as count
    FROM matches m
    JOIN teams ht ON m.home_team_id = ht.team_id
    JOIN teams at ON m.away_team_id = at.team_id
    JOIN leagues l ON m.league_id = l.league_id
    GROUP BY l.league_name, m.season, ht.team_name, at.team_name, m.home_goals, m.away_goals
    HAVING COUNT(*) > 1
    ORDER BY count DESC
    """
    
    cursor.execute(query)
    duplicates = cursor.fetchall()
    
    if duplicates:
        print(f"\n⚠️ Found {len(duplicates)} duplicate match records!")
        print("\nSample duplicates:")
        for dup in duplicates[:10]:
            print(f"  {dup[0]} {dup[1]}: {dup[2]} vs {dup[3]} ({dup[4]}-{dup[5]}) - stored {dup[6]} times")
    else:
        print("\n✅ No duplicate match records found!")
    
    # Check total matches per team per season
    print("\n📊 Matches per team per season:")
    query2 = """
    SELECT 
        l.league_name,
        m.season,
        t.team_name,
        COUNT(DISTINCT m.match_id) as matches_played
    FROM (
        SELECT match_id, league_id, season, home_team_id as team_id FROM matches
        UNION ALL
        SELECT match_id, league_id, season, away_team_id as team_id FROM matches
    ) m
    JOIN teams t ON m.team_id = t.team_id
    JOIN leagues l ON m.league_id = l.league_id
    WHERE l.league_name = 'Premier League' AND m.season IN ('2425', '2526')
    GROUP BY l.league_name, m.season, t.team_name
    ORDER BY m.season DESC, matches_played DESC
    LIMIT 10
    """
    
    cursor.execute(query2)
    results = cursor.fetchall()
    
    print("\nPremier League recent seasons:")
    for row in results:
        season_display = f"20{row[1][:2]}-{row[1][2:]}" if len(row[1]) == 4 else row[1]
        print(f"  {season_display}: {row[2]} - {row[3]} matches")
        if row[1] == '2425' and row[3] != 38:
            print(f"    ⚠️ Expected 38 matches for complete season!")
        elif row[1] == '2526' and row[3] > 15:
            print(f"    ℹ️ Current season in progress")
    
    conn.close()
    return len(duplicates) if duplicates else 0

def remove_duplicates():
    """Remove duplicate matches, keeping only one copy of each"""
    db_path = Path("data/football.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n🔧 Removing duplicate matches...")
    
    # Find and delete duplicates, keeping the one with the lowest match_id
    # This ensures we keep one copy of each unique match
    query = """
    DELETE FROM matches
    WHERE match_id NOT IN (
        SELECT MIN(match_id)
        FROM matches
        GROUP BY league_id, season, home_team_id, away_team_id, home_goals, away_goals
    )
    """
    
    cursor.execute(query)
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    
    print(f"✅ Removed {deleted} duplicate match records!")
    return deleted

def check_total_matches():
    """Check total unique matches in database"""
    db_path = Path("data/football.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    query = """
    SELECT COUNT(DISTINCT match_id) as total_matches
    FROM matches
    """
    
    cursor.execute(query)
    total = cursor.fetchone()[0]
    
    print(f"\n📊 Total unique matches in database: {total:,}")
    
    # Check by league
    query2 = """
    SELECT 
        l.league_name,
        COUNT(DISTINCT m.match_id) as matches
    FROM matches m
    JOIN leagues l ON m.league_id = l.league_id
    GROUP BY l.league_name
    ORDER BY matches DESC
    """
    
    cursor.execute(query2)
    results = cursor.fetchall()
    
    print("\nMatches per league:")
    for row in results:
        print(f"  {row[0]}: {row[1]:,} matches")
    
    conn.close()

if __name__ == "__main__":
    print("=" * 70)
    print("DATABASE DUPLICATE CHECK & CLEANUP")
    print("=" * 70)
    
    duplicate_count = check_duplicates()
    check_total_matches()
    
    if duplicate_count > 0:
        print("\n" + "=" * 70)
        response = input(f"\n❓ Found {duplicate_count} duplicate records. Remove them? (y/n): ")
        if response.lower() == 'y':
            remove_duplicates()
            print("\n✅ Database cleaned! Re-checking...")
            print("=" * 70)
            check_duplicates()
            check_total_matches()
        else:
            print("❌ Skipped duplicate removal.")
    else:
        print("\n" + "=" * 70)
        print("✅ Database is clean - no duplicate records found!")
        print("=" * 70)