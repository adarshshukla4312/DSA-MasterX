"""
GritX — Database Schema & Initialization
"""
import sqlite3
import json
from pathlib import Path


def get_connection(db_path: str | Path) -> sqlite3.Connection:
    """Get a database connection with row factory enabled."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path: str | Path) -> None:
    """Create all tables if they don't exist and run column migrations if needed."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS lectures (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            filename TEXT,
            video_path TEXT,
            transcript_path TEXT,
            topics TEXT DEFAULT '[]',
            techniques TEXT DEFAULT '[]',
            difficulty TEXT DEFAULT '',
            key_moments TEXT DEFAULT '[]',
            problems_discussed TEXT DEFAULT '[]',
            concept_ladder TEXT DEFAULT '[]',
            mcqs TEXT DEFAULT '[]',
            flashcards TEXT DEFAULT '[]',
            pipeline_hash TEXT DEFAULT '',
            status TEXT DEFAULT 'new',
            processed_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS problems (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            platform TEXT DEFAULT 'LeetCode',
            url TEXT DEFAULT '',
            difficulty TEXT DEFAULT 'Medium',
            patterns TEXT DEFAULT '[]',
            related_variants TEXT DEFAULT '[]',
            prerequisites TEXT DEFAULT '[]',
            description TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS lecture_problem_matches (
            lecture_id TEXT REFERENCES lectures(id),
            problem_id TEXT REFERENCES problems(id),
            confirmed INTEGER DEFAULT 0,
            timestamp_start TEXT DEFAULT '',
            timestamp_end TEXT DEFAULT '',
            match_reasoning TEXT DEFAULT '',
            match_score REAL DEFAULT 0.0,
            PRIMARY KEY (lecture_id, problem_id)
        );

        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            problem_id TEXT REFERENCES problems(id),
            solved INTEGER DEFAULT 0,
            difficulty_felt INTEGER DEFAULT 3,
            time_min INTEGER DEFAULT 0,
            used_hint INTEGER DEFAULT 0,
            date TEXT,
            notes TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS revision_schedule (
            pattern TEXT PRIMARY KEY,
            next_due_date TEXT,
            interval REAL DEFAULT 1.0,
            ease_factor REAL DEFAULT 2.5,
            repetitions INTEGER DEFAULT 0,
            last_reviewed TEXT
        );
    """)

    # Migrations for existing SQLite database
    existing_cols = {row["name"] for row in cursor.execute("PRAGMA table_info(lectures)").fetchall()}
    if "concept_ladder" not in existing_cols:
        cursor.execute("ALTER TABLE lectures ADD COLUMN concept_ladder TEXT DEFAULT '[]'")
    if "mcqs" not in existing_cols:
        cursor.execute("ALTER TABLE lectures ADD COLUMN mcqs TEXT DEFAULT '[]'")
    if "flashcards" not in existing_cols:
        cursor.execute("ALTER TABLE lectures ADD COLUMN flashcards TEXT DEFAULT '[]'")
    if "pipeline_hash" not in existing_cols:
        cursor.execute("ALTER TABLE lectures ADD COLUMN pipeline_hash TEXT DEFAULT ''")

    # Migration for problems table: embedding vector
    existing_problem_cols = {row["name"] for row in cursor.execute("PRAGMA table_info(problems)").fetchall()}
    if "embedding" not in existing_problem_cols:
        cursor.execute("ALTER TABLE problems ADD COLUMN embedding BLOB")

    conn.commit()
    conn.close()


def load_problems_from_json(db_path: str | Path, json_path: str | Path) -> int:
    """Load problems from problems.json into the database. Returns count of new problems added."""
    json_path = Path(json_path)
    if not json_path.exists():
        return 0

    with open(json_path, "r", encoding="utf-8") as f:
        problems = json.load(f)

    conn = get_connection(db_path)
    cursor = conn.cursor()
    count = 0

    for p in problems:
        try:
            cursor.execute(
                """INSERT OR IGNORE INTO problems 
                   (id, title, platform, url, difficulty, patterns, related_variants, prerequisites, description)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    p["id"],
                    p["title"],
                    p.get("platform", "LeetCode"),
                    p.get("url", ""),
                    p.get("difficulty", "Medium"),
                    json.dumps(p.get("patterns", [])),
                    json.dumps(p.get("related_variants", [])),
                    json.dumps(p.get("prerequisites", [])),
                    p.get("description", ""),
                ),
            )
            if cursor.rowcount > 0:
                count += 1
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    conn.close()
    return count


# ─── Helper functions ─────────────────────────────────────────────────────────

def get_lecture(db_path: str | Path, lecture_id: str) -> dict | None:
    """Get a single lecture by ID."""
    conn = get_connection(db_path)
    row = conn.execute("SELECT * FROM lectures WHERE id = ?", (lecture_id,)).fetchone()
    conn.close()
    if row:
        d = dict(row)
        for key in ["topics", "techniques", "key_moments", "problems_discussed", "concept_ladder", "mcqs", "flashcards"]:
            if d.get(key):
                try:
                    d[key] = json.loads(d[key])
                except (json.JSONDecodeError, TypeError):
                    d[key] = []
            else:
                d[key] = []
        return d
    return None


def get_all_lectures(db_path: str | Path) -> list[dict]:
    """Get all lectures."""
    conn = get_connection(db_path)
    rows = conn.execute("SELECT * FROM lectures ORDER BY id").fetchall()
    conn.close()
    results = []
    for row in rows:
        d = dict(row)
        for key in ["topics", "techniques", "key_moments", "problems_discussed", "concept_ladder", "mcqs", "flashcards"]:
            if d.get(key):
                try:
                    d[key] = json.loads(d[key])
                except (json.JSONDecodeError, TypeError):
                    d[key] = []
            else:
                d[key] = []
        results.append(d)
    return results


def upsert_lecture(db_path: str | Path, lecture: dict) -> None:
    """Insert or update a lecture."""
    conn = get_connection(db_path)
    data = lecture.copy()
    for key in ["topics", "techniques", "key_moments", "problems_discussed", "concept_ladder", "mcqs", "flashcards"]:
        if key in data and isinstance(data[key], (list, dict)):
            data[key] = json.dumps(data[key])
        elif key not in data:
            data[key] = '[]'

    if "pipeline_hash" not in data:
        data["pipeline_hash"] = ""
    if "status" not in data:
        data["status"] = "new"
    if "processed_at" not in data:
        data["processed_at"] = None

    conn.execute(
        """INSERT OR REPLACE INTO lectures 
           (id, title, filename, video_path, transcript_path, topics, techniques, 
            difficulty, key_moments, problems_discussed, concept_ladder, mcqs, flashcards, pipeline_hash, status, processed_at)
           VALUES (:id, :title, :filename, :video_path, :transcript_path, :topics, 
                   :techniques, :difficulty, :key_moments, :problems_discussed, 
                   :concept_ladder, :mcqs, :flashcards, :pipeline_hash, :status, :processed_at)""",
        data,
    )
    conn.commit()
    conn.close()


def get_all_problems(db_path: str | Path) -> list[dict]:
    """Get all problems from the database."""
    conn = get_connection(db_path)
    rows = conn.execute("SELECT * FROM problems ORDER BY id").fetchall()
    conn.close()
    results = []
    for row in rows:
        d = dict(row)
        for key in ["patterns", "related_variants", "prerequisites"]:
            if d.get(key):
                try:
                    d[key] = json.loads(d[key])
                except (json.JSONDecodeError, TypeError):
                    d[key] = []
            else:
                d[key] = []
        results.append(d)
    return results


def get_unconfirmed_matches(db_path: str | Path) -> list[dict]:
    """Get all unconfirmed lecture-problem matches."""
    conn = get_connection(db_path)
    rows = conn.execute(
        """SELECT lpm.*, l.title as lecture_title, p.title as problem_title, 
                  p.difficulty as problem_difficulty, p.patterns as problem_patterns, p.url as problem_url
           FROM lecture_problem_matches lpm
           JOIN lectures l ON lpm.lecture_id = l.id
           JOIN problems p ON lpm.problem_id = p.id
           WHERE lpm.confirmed = 0
           ORDER BY lpm.lecture_id, lpm.match_score DESC"""
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def confirm_match(db_path: str | Path, lecture_id: str, problem_id: str) -> None:
    """Confirm a lecture-problem match and remove other candidates for that lecture."""
    conn = get_connection(db_path)
    conn.execute(
        "UPDATE lecture_problem_matches SET confirmed = 1 WHERE lecture_id = ? AND problem_id = ?",
        (lecture_id, problem_id),
    )
    conn.execute(
        "DELETE FROM lecture_problem_matches WHERE lecture_id = ? AND problem_id != ? AND confirmed = 0",
        (lecture_id, problem_id),
    )
    conn.execute("UPDATE lectures SET status = 'matched' WHERE id = ?", (lecture_id,))
    conn.commit()
    conn.close()


def log_attempt(db_path: str | Path, attempt: dict) -> None:
    """Log a solve attempt."""
    conn = get_connection(db_path)
    conn.execute(
        """INSERT INTO attempts (problem_id, solved, difficulty_felt, time_min, used_hint, date, notes)
           VALUES (:problem_id, :solved, :difficulty_felt, :time_min, :used_hint, :date, :notes)""",
        attempt,
    )
    conn.commit()
    conn.close()


def get_attempts(db_path: str | Path, problem_id: str = None) -> list[dict]:
    """Get attempts, optionally filtered by problem_id."""
    conn = get_connection(db_path)
    if problem_id:
        rows = conn.execute(
            "SELECT * FROM attempts WHERE problem_id = ? ORDER BY date DESC", (problem_id,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM attempts ORDER BY date DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_solved_problem_ids(db_path: str | Path) -> set[str]:
    """Get IDs of all problems that have been solved at least once."""
    conn = get_connection(db_path)
    rows = conn.execute("SELECT DISTINCT problem_id FROM attempts WHERE solved = 1").fetchall()
    conn.close()
    return {row["problem_id"] for row in rows}


def get_confirmed_matches_for_lecture(db_path: str | Path, lecture_id: str) -> list[dict]:
    """Get confirmed problem matches for a lecture."""
    conn = get_connection(db_path)
    rows = conn.execute(
        """SELECT lpm.*, p.title, p.platform, p.url, p.difficulty, p.patterns
           FROM lecture_problem_matches lpm
           JOIN problems p ON lpm.problem_id = p.id
           WHERE lpm.lecture_id = ? AND lpm.confirmed = 1""",
        (lecture_id,),
    ).fetchall()
    conn.close()
    results = []
    for row in rows:
        d = dict(row)
        if d.get("patterns"):
            try:
                d["patterns"] = json.loads(d["patterns"])
            except (json.JSONDecodeError, TypeError):
                d["patterns"] = []
        results.append(d)
    return results
