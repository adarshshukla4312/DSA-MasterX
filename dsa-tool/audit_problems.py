import json
from db.schema import get_connection

conn = get_connection("data/dsa_tool.db")

total = conn.execute("SELECT count(*) FROM problems").fetchone()[0]
print(f"Total problems: {total}")

empty_titles = conn.execute("SELECT count(*) FROM problems WHERE title IS NULL OR trim(title) = ''").fetchone()[0]
print(f"Empty/null titles: {empty_titles}")

empty_ids = conn.execute("SELECT count(*) FROM problems WHERE id IS NULL OR trim(id) = ''").fetchone()[0]
print(f"Empty/null ids: {empty_ids}")

rows = conn.execute("SELECT id, patterns FROM problems").fetchall()
bad_patterns = 0
for r in rows:
    try:
        p = json.loads(r["patterns"])
        if not isinstance(p, list):
            bad_patterns += 1
    except Exception:
        bad_patterns += 1
print(f"Corrupted pattern JSON rows: {bad_patterns}")

diffs = conn.execute("SELECT difficulty, count(*) FROM problems GROUP BY difficulty").fetchall()
print("Difficulty breakdown:", dict(diffs))

platforms = conn.execute("SELECT platform, count(*) FROM problems GROUP BY platform").fetchall()
print("Platform breakdown:", dict(platforms))

with open("data/problems.json", "r", encoding="utf-8") as f:
    json_data = json.load(f)
print(f"problems.json records: {len(json_data)} (Valid JSON!)")

conn.close()
