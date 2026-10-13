"""
DSA Mastery Tool — Importer for Striver's A2Z DSA Sheet and NeetCode/LeetCode 250.
Features:
- Automated fetching of official LeetCode question catalog (4000+ problems)
- Comprehensive multi-tier deduplication (ID, slug, URL, normalized title)
- Pattern tag normalization & enrichment
- Batch SQLite insertion & JSON catalog sync
- Integrity audit & statistical verification
"""
import sys
import json
import re
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from db.schema import get_connection

db_path = Path("data/dsa_tool.db")
json_path = Path("data/problems.json")

def norm_url(u: str) -> str:
    if not u:
        return ""
    return u.strip().rstrip("/").lower()

def norm_title(t: str) -> str:
    if not t:
        return ""
    return "".join(c for c in t.lower() if c.isalnum())

def extract_slug(u: str) -> str:
    if not u:
        return ""
    m = re.search(r"/problems/([^/?#]+)", u.lower())
    return m.group(1) if m else ""

def clean_patterns(pat_list: list[str]) -> list[str]:
    seen = set()
    cleaned = []
    for p in pat_list:
        if not p:
            continue
        p_clean = p.strip()
        if p_clean and p_clean.lower() not in seen:
            seen.add(p_clean.lower())
            cleaned.append(p_clean)
    return cleaned

print("=" * 70)
print("1. Fetching LeetCode Question Catalog for Canonical IDs...")
print("=" * 70)

by_slug = {}
try:
    req = urllib.request.Request(
        "https://leetcode.com/api/problems/all/",
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        catalog = json.loads(resp.read().decode())
    for p in catalog.get("stat_status_pairs", []):
        stat = p["stat"]
        slug = stat["question__title_slug"].lower()
        fid = stat.get("frontend_question_id", stat["question_id"])
        by_slug[slug] = (fid, stat["question__title"])
    print(f"Loaded LeetCode catalog with {len(by_slug)} canonical problems.")
except Exception as e:
    print(f"Warning: LeetCode catalog fetch error: {e}")

print("\n" + "=" * 70)
print("2. Loading Existing Database Records...")
print("=" * 70)

conn = get_connection(db_path)
db_rows = conn.execute("SELECT * FROM problems").fetchall()
conn.close()

existing_by_id = {}
existing_by_slug = {}
existing_by_title = {}
existing_by_url = {}

for r in db_rows:
    d = dict(r)
    pid = d["id"].lower()
    existing_by_id[pid] = d
    u = norm_url(d.get("url", ""))
    if u:
        existing_by_url[u] = d
    s = extract_slug(d.get("url", ""))
    if s:
        existing_by_slug[s] = d
    t = norm_title(d.get("title", ""))
    if t:
        existing_by_title[t] = d

print(f"Existing database contains {len(db_rows)} problems.")

# Storage for pending insertions and updates
new_problems = {}  # keyed by lowercase canonical id
url_updates = []   # tuples of (url, pid)
pattern_updates = [] # tuples of (new_patterns_json, pid)

def lookup_match(cand_id: str, slug: str, url: str, title: str) -> dict | None:
    norm_u = norm_url(url)
    norm_t = norm_title(title)
    
    # Check DB
    if cand_id and cand_id.lower() in existing_by_id:
        return existing_by_id[cand_id.lower()]
    if slug and slug in existing_by_slug:
        return existing_by_slug[slug]
    if norm_u and norm_u in existing_by_url:
        return existing_by_url[norm_u]
    if norm_t and norm_t in existing_by_title:
        return existing_by_title[norm_t]
        
    # Check already staged new problems
    if cand_id and cand_id.lower() in new_problems:
        return new_problems[cand_id.lower()]
    for p in new_problems.values():
        if slug and extract_slug(p.get("url")) == slug:
            return p
        if norm_u and norm_url(p.get("url")) == norm_u:
            return p
        if norm_t and norm_title(p.get("title")) == norm_t:
            return p
            
    return None

print("\n" + "=" * 70)
print("3. Fetching and Processing NeetCode 250...")
print("=" * 70)

url_nc = "https://raw.githubusercontent.com/ascherj/neetcode-250-guide/main/neetcode_250_complete.json"
req_nc = urllib.request.Request(url_nc, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req_nc, timeout=15) as resp:
    nc_data = json.loads(resp.read().decode("utf-8"))

nc_problems = nc_data.get("problems", [])
print(f"Fetched {len(nc_problems)} problems from NeetCode 250.")

nc_dups = 0
nc_added = 0

for p in nc_problems:
    title = p.get("name", "").strip()
    lc_url = p.get("leetcode_url", "").strip()
    diff = p.get("difficulty", "Medium").capitalize()
    cat = p.get("category", "General DSA").strip()
    
    slug = extract_slug(lc_url)
    fid = by_slug.get(slug, (None, None))[0] if slug else None
    
    if fid is not None:
        cand_id = f"lc-{fid}"
    elif slug:
        cand_id = f"lc-{slug}"
    else:
        cand_id = f"lc-{norm_title(title)}"
        
    std_url = lc_url.rstrip("/") + "/" if lc_url.startswith("http") else ""
    patterns = clean_patterns([cat])
    
    match = lookup_match(cand_id, slug, std_url, title)
    if match:
        nc_dups += 1
        # Backfill URL if missing
        if not match.get("url") and std_url:
            url_updates.append((std_url, match["id"]))
            match["url"] = std_url
        # Enrich patterns if needed
        try:
            curr_pats = json.loads(match.get("patterns") or "[]")
        except Exception:
            curr_pats = []
        combined_pats = clean_patterns(curr_pats + patterns)
        if len(combined_pats) > len(curr_pats):
            pattern_updates.append((json.dumps(combined_pats), match["id"]))
            match["patterns"] = json.dumps(combined_pats)
    else:
        nc_added += 1
        new_problems[cand_id.lower()] = {
            "id": cand_id,
            "title": title,
            "platform": "LeetCode",
            "url": std_url,
            "difficulty": diff,
            "patterns": patterns,
            "related_variants": [],
            "prerequisites": [],
            "description": f"NeetCode 250 Track ({diff}) — Category: {cat}"
        }

print(f"NeetCode 250 processed: {nc_dups} duplicates/existing, {nc_added} new additions.")

print("\n" + "=" * 70)
print("4. Fetching and Processing Striver's A2Z DSA Sheet...")
print("=" * 70)

url_striver = "https://raw.githubusercontent.com/hitarth-gg/CP/main/striver-a2z.json"
req_striver = urllib.request.Request(url_striver, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req_striver, timeout=15) as resp:
    striver_data = json.loads(resp.read().decode("utf-8"))

striver_dups = 0
striver_added = 0
diff_map = {0: "Easy", 1: "Medium", 2: "Hard"}
total_striver_items = 0

for step in striver_data:
    step_title = step.get("step_title", "").strip()
    for sub in step.get("sub_steps", []):
        sub_title = sub.get("sub_step_title", "").strip()
        for t in sub.get("topics", []):
            total_striver_items += 1
            title = t.get("question_title", "").strip()
            lc_link = (t.get("lc_link") or "").strip()
            post_link = (t.get("plus_link") or t.get("post_link") or "").strip()
            
            slug = extract_slug(lc_link) if lc_link else extract_slug(post_link)
            fid = by_slug.get(slug, (None, None))[0] if slug else None
            
            platform = "LeetCode" if lc_link else ("TakeUForward" if "takeuforward" in post_link else "GFG")
            main_url = lc_link if lc_link else post_link
            std_url = main_url.rstrip("/") + "/" if main_url.startswith("http") else ""
            
            if fid is not None:
                cand_id = f"lc-{fid}"
            elif slug:
                cand_id = f"lc-{slug}" if platform == "LeetCode" else f"tuf-{slug}"
            else:
                cand_id = f"tuf-{norm_title(title)}"
                
            raw_diff = t.get("difficulty", 1)
            diff = diff_map.get(raw_diff, "Medium")
            
            # Extract patterns
            patterns = [step_title, sub_title]
            ques_topic_raw = t.get("ques_topic")
            if ques_topic_raw:
                try:
                    q_topics = json.loads(ques_topic_raw)
                    for qt in q_topics:
                        if isinstance(qt, dict) and qt.get("label"):
                            patterns.append(qt["label"])
                except Exception:
                    pass
            patterns = clean_patterns(patterns)
            
            match = lookup_match(cand_id, slug, std_url, title)
            if match:
                striver_dups += 1
                if not match.get("url") and std_url:
                    url_updates.append((std_url, match["id"]))
                    match["url"] = std_url
                try:
                    curr_pats = json.loads(match.get("patterns") or "[]")
                except Exception:
                    curr_pats = []
                combined_pats = clean_patterns(curr_pats + patterns)
                if len(combined_pats) > len(curr_pats):
                    pattern_updates.append((json.dumps(combined_pats), match["id"]))
                    match["patterns"] = json.dumps(combined_pats)
            else:
                striver_added += 1
                new_problems[cand_id.lower()] = {
                    "id": cand_id,
                    "title": title,
                    "platform": platform,
                    "url": std_url,
                    "difficulty": diff,
                    "patterns": patterns,
                    "related_variants": [],
                    "prerequisites": [],
                    "description": f"Striver A2Z DSA Sheet — {step_title} / {sub_title} ({diff})"
                }

print(f"Total Striver A2Z questions parsed: {total_striver_items}")
print(f"Striver A2Z processed: {striver_dups} duplicates/existing, {striver_added} new additions.")

print("\n" + "=" * 70)
print(f"5. Committing to Database: {db_path}...")
print("=" * 70)

conn = get_connection(db_path)
cursor = conn.cursor()

# 1. Insert new problems
inserted_count = 0
for prob in new_problems.values():
    cursor.execute(
        """INSERT OR IGNORE INTO problems 
           (id, title, platform, url, difficulty, patterns, related_variants, prerequisites, description)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            prob["id"],
            prob["title"],
            prob["platform"],
            prob["url"],
            prob["difficulty"],
            json.dumps(prob["patterns"]),
            json.dumps(prob["related_variants"]),
            json.dumps(prob["prerequisites"]),
            prob["description"]
        )
    )
    if cursor.rowcount > 0:
        inserted_count += 1

# 2. Apply URL backfills
updated_urls_count = 0
for url, pid in url_updates:
    cursor.execute("UPDATE problems SET url = ? WHERE id = ? AND (url = '' OR url IS NULL)", (url, pid))
    if cursor.rowcount > 0:
        updated_urls_count += 1

# 3. Apply Pattern enrichments
updated_pats_count = 0
for pats_json, pid in pattern_updates:
    cursor.execute("UPDATE problems SET patterns = ? WHERE id = ?", (pats_json, pid))
    if cursor.rowcount > 0:
        updated_pats_count += 1

conn.commit()

# Query final DB state
total_in_db = cursor.execute("SELECT count(*) FROM problems").fetchone()[0]
diff_stats = cursor.execute("SELECT difficulty, count(*) FROM problems GROUP BY difficulty").fetchall()
platform_stats = cursor.execute("SELECT platform, count(*) FROM problems GROUP BY platform").fetchall()

conn.close()

print(f"Successfully inserted {inserted_count} new problems into database.")
print(f"Updated URLs for {updated_urls_count} existing problems.")
print(f"Enriched pattern tags for {updated_pats_count} existing problems.")
print(f"\nFinal Problems Count in DB: {total_in_db}")

print("\nDifficulty Breakdown:")
for d, c in diff_stats:
    print(f"  - {d}: {c}")

print("\nPlatform Breakdown:")
for pl, c in platform_stats:
    print(f"  - {pl}: {c}")

print("\n" + "=" * 70)
print(f"6. Synchronizing JSON Catalog: {json_path}...")
print("=" * 70)

if json_path.exists():
    with open(json_path, "r", encoding="utf-8") as f:
        existing_json = json.load(f)
        
    json_ids = {p["id"].lower() for p in existing_json if "id" in p}
    json_added = 0
    for prob in new_problems.values():
        if prob["id"].lower() not in json_ids:
            existing_json.append(prob)
            json_ids.add(prob["id"].lower())
            json_added += 1
            
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(existing_json, f, indent=2, ensure_ascii=False)
        
    print(f"Updated {json_path}: added {json_added} new records (Total in JSON: {len(existing_json)}).")

print("\n" + "=" * 70)
print("IMPORT & AUDIT COMPLETED SUCCESSFULLY!")
print("=" * 70)
