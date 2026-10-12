"""Remove mis-tagged matches: teams with far fewer matches than the league leaders."""
import sqlite3
from collections import Counter

conn = sqlite3.connect('data/football.db')
cur = conn.cursor()

cur.execute("SELECT league_id, league_name FROM leagues")
leagues = cur.fetchall()

names = dict(cur.execute("SELECT team_id, team_name FROM teams").fetchall())
to_delete = []

for league_id, league_name in leagues:
    seasons = [r[0] for r in cur.execute(
        "SELECT DISTINCT season FROM matches WHERE league_id = ?", (league_id,))]
    for season in seasons:
        rows = cur.execute(
            "SELECT match_id, home_team_id, away_team_id FROM matches "
            "WHERE league_id = ? AND season = ?", (league_id, season)).fetchall()

        counts = Counter()
        for _, h, a in rows:
            counts[h] += 1
            counts[a] += 1

        max_played = max(counts.values())
        if max_played < 4:
            continue

        outliers = {t for t, c in counts.items() if c < max_played * 0.5}
        if not outliers:
            continue

        bad = [m for m, h, a in rows if h in outliers or a in outliers]
        to_delete.extend(bad)
        print(f"\n{league_name} {season}: {len(outliers)} outlier teams, {len(bad)} matches")
        print("  " + ", ".join(sorted(names[t] for t in outliers)))

if not to_delete:
    print("\nNo outliers found.")
else:
    if input(f"\nDelete {len(to_delete)} matches? (y/n): ").lower() == 'y':
        cur.executemany("DELETE FROM matches WHERE match_id = ?", [(m,) for m in to_delete])
        cur.execute("""DELETE FROM teams WHERE team_id NOT IN (
                         SELECT home_team_id FROM matches
                         UNION SELECT away_team_id FROM matches)""")
        conn.commit()
        print("Done.")

conn.close()