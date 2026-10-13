import csv
import json
import re
import urllib.request
from pathlib import Path
from db.schema import get_connection

csv_path = Path(r"C:\Users\adars\Downloads\Google_LeetCode_Questions_3Months.csv")
db_path = Path("data/dsa_tool.db")
json_path = Path("data/problems.json")

print("1. Fetching LeetCode question catalog for official question IDs...")
by_slug = {}
try:
    req = urllib.request.Request(
        "https://leetcode.com/api/problems/all/",
        headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        catalog = json.loads(response.read().decode())
    for p in catalog.get("stat_status_pairs", []):
        stat = p["stat"]
        slug = stat["question__title_slug"].lower()
        fid = stat.get("frontend_question_id", stat["question_id"])
        by_slug[slug] = fid
    print(f"Catalog loaded: {len(by_slug)} problems.")
except Exception as e:
    print(f"Warning: LeetCode catalog fetch failed: {e}")

# 2. Get existing DB problems
conn = get_connection(db_path)
existing_rows = conn.execute("SELECT id, title, url, patterns, difficulty FROM problems").fetchall()
conn.close()

def norm_url(u):
    if not u:
        return ""
    return u.strip().rstrip("/").lower()

def norm_title(t):
    if not t:
        return ""
    return "".join(c for c in t.lower() if c.isalnum())

def extract_slug(u):
    if not u:
        return ""
    m = re.search(r"/problems/([^/?#]+)", u.lower())
    return m.group(1) if m else ""

existing_by_id = {r["id"].lower(): r for r in existing_rows}
existing_by_slug = {extract_slug(r["url"]): r for r in existing_rows if extract_slug(r["url"])}
existing_by_title = {norm_title(r["title"]): r for r in existing_rows if r["title"]}
existing_by_url = {norm_url(r["url"]): r for r in existing_rows if r["url"]}

print(f"Existing DB problems count: {len(existing_rows)}")

# 3. Read and process CSV
with open(csv_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    csv_rows = list(reader)

duplicates = []
to_insert = []
url_updates = []

for r in csv_rows:
    title = r["Title"].strip()
    raw_link = r["Link"].strip()
    diff = r["Difficulty"].strip().title()
    topics_raw = r.get("Topics", "")
    topics = [t.strip() for t in topics_raw.split(",") if t.strip()]

    slug = extract_slug(raw_link)
    norm_u = norm_url(raw_link)
    norm_t = norm_title(title)

    fid = by_slug.get(slug)
    candidate_id = f"lc-{fid}" if fid is not None else (f"lc-{slug}" if slug else f"lc-{norm_t}")

    # Check duplicate
    dup_reason = None
    existing_match = None

    if candidate_id.lower() in existing_by_id:
        existing_match = existing_by_id[candidate_id.lower()]
        dup_reason = f"ID match ({existing_match['id']})"
    elif norm_u and norm_u in existing_by_url:
        existing_match = existing_by_url[norm_u]
        dup_reason = f"URL match ({existing_match['id']}: {existing_match['title']})"
    elif slug and slug in existing_by_slug:
        existing_match = existing_by_slug[slug]
        dup_reason = f"Slug match ({existing_match['id']}: {existing_match['title']})"
    elif norm_t in existing_by_title:
        existing_match = existing_by_title[norm_t]
        dup_reason = f"Title match ({existing_match['id']}: {existing_match['title']})"

    if existing_match:
        duplicates.append({
            "csv_title": title,
            "csv_url": raw_link,
            "reason": dup_reason,
            "existing_id": existing_match["id"],
            "existing_title": existing_match["title"]
        })
        # If existing record has empty url, update it
        if not existing_match["url"] and raw_link:
            std_url = raw_link.rstrip("/") + "/"
            url_updates.append((std_url, existing_match["id"]))
    else:
        std_url = raw_link.rstrip("/") + "/" if raw_link.startswith("http") else raw_link
        to_insert.append({
            "id": candidate_id,
            "title": title,
            "platform": "LeetCode",
            "url": std_url,
            "difficulty": diff,
            "patterns": topics,
            "related_variants": [],
            "prerequisites": [],
            "description": f"Google Interview Question ({diff}). Topics: {', '.join(topics)}."
        })

print("\n" + "=" * 50)
print(f"Total CSV questions: {len(csv_rows)}")
print(f"Duplicates filtered out: {len(duplicates)}")
print(f"New problems to import: {len(to_insert)}")
print(f"Existing records updated with URL: {len(url_updates)}")
print("=" * 50)

# 4. Insert into database
conn = get_connection(db_path)
cursor = conn.cursor()

inserted_count = 0
for p in to_insert:
    cursor.execute(
        """INSERT OR IGNORE INTO problems 
           (id, title, platform, url, difficulty, patterns, related_variants, prerequisites, description)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            p["id"],
            p["title"],
            p["platform"],
            p["url"],
            p["difficulty"],
            json.dumps(p["patterns"]),
            json.dumps(p["related_variants"]),
            json.dumps(p["prerequisites"]),
            p["description"]
        )
    )
    if cursor.rowcount > 0:
        inserted_count += 1

# Update missing URLs on existing problems
for url, pid in url_updates:
    cursor.execute("UPDATE problems SET url = ? WHERE id = ? AND (url = '' OR url IS NULL)", (url, pid))

conn.commit()

# Verify new DB total
new_total = cursor.execute("SELECT count(*) as c FROM problems").fetchone()["c"]
conn.close()

print(f"\nSuccessfully inserted {inserted_count} new problems into {db_path}.")
print(f"New total problems in database: {new_total}")

# 5. Also update data/problems.json
if json_path.exists():
    with open(json_path, "r", encoding="utf-8") as f:
        existing_json_data = json.load(f)
    
    existing_json_ids = {p["id"].lower() for p in existing_json_data if "id" in p}
    added_to_json = 0
    for p in to_insert:
        if p["id"].lower() not in existing_json_ids:
            existing_json_data.append(p)
            existing_json_ids.add(p["id"].lower())
            added_to_json += 1
            
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(existing_json_data, f, indent=2, ensure_ascii=False)
        
    print(f"Updated {json_path}: added {added_to_json} new entries (total: {len(existing_json_data)}).")
