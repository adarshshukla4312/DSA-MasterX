# DSA Mastery Tool — Project Plan

**Goal:** Turn 48 (and growing) offline Scaler DSA lectures into a personalized, ordered practice sheet — with correct problem identification, next-problem recommendations, and spaced revision.

---

## 1. Problem Statement

You have 48 offline lecture videos (and more coming weekly). For each lecture you need to know:

1. **What problem(s) were actually discussed** — and specifically, *which exact version* of that problem (e.g. not just "majority element" but LeetCode 169, Boyer-Moore variant, not the "majority element II" variant).
2. **What to solve next** to reinforce that concept, in a sensible order (easy → hard).
3. **When to revisit** concepts you've already covered, before they decay.

This is three connected engines, not one: **Identify → Recommend → Revise.**

---

## 2. Scope

### In scope for MVP
- Transcribe lecture → extract concepts + the specific problem(s) discussed
- Match extracted problem to a canonical entry in a curated problem database (with confirmation step, since auto-matching won't be 100% reliable)
- Recommend an ordered practice set (3–5 problems) per lecture
- Log your solve attempts (solved/unsolved, difficulty felt, time, hint used)
- Basic revision queue using spaced repetition

### Explicitly out of scope for MVP (Version 2+)
- Semantic embedding search (start with tag/keyword matching — cheaper, more debuggable, good enough at ~150 problems)
- Web UI (CLI or single-page Streamlit app first)
- Prerequisite-gap detection ("you haven't mastered X, do that first")
- Multi-user / hosting this for other students

---

## 3. High-Level Architecture

```
Lecture video (.mp4, offline)
        │
        ▼
[1] Extract audio  ──────────────► ffmpeg
        │
        ▼
[2] Transcribe  ─────────────────► Whisper (local, whisper.cpp or faster-whisper)
        │
        ▼
[3] Transcript stored (raw + chunked)
        │
        ▼
[4] LLM Pass #1 — Concept Extraction
        (topics, patterns, techniques, difficulty signals)
        │
        ▼
[5] LLM Pass #2 — Problem Identification
        (what exact problem was walked through on the whiteboard/editor?)
        │
        ▼
[6] Match against Curated Problem DB
        (keyword/tag match → top 3 candidates)
        │
        ▼
[7] YOU confirm the match (one click) ──► stored permanently, never re-asked
        │
        ▼
[8] Recommendation Engine
        (same pattern, ordered by difficulty, excludes already-solved)
        │
        ▼
[9] Output: Lecture Practice Sheet
        │
        ▼
[10] You solve problems → log outcome
        │
        ▼
[11] Revision Engine (spaced repetition) schedules re-tests
```

Steps 1–3 run once per lecture (batch job). Steps 4–9 are where the actual product value is.

---

## 4. Core Components

### 4.1 Lecture Ingestion & Transcription
- `ffmpeg` extracts audio track from each `.mp4`
- `faster-whisper` (local, runs on CPU/GPU, no API cost) transcribes to text with timestamps
- Store transcript as JSON: `{lecture_id, segments: [{start, end, text}]}`
- Timestamps matter — when you confirm "yes, this is LeetCode 169," you can also store *when in the video* it was discussed, so you can jump back to that exact explanation later.

### 4.2 Concept Extraction (LLM Pass #1)
Feed the full transcript (or chunks if too long) to an LLM with a structured prompt. Output: topics, named techniques (e.g. "Boyer-Moore voting", "XOR trick"), and a difficulty estimate. This pass is cheap and mostly reliable — LLMs are good at "what topics did this text cover."

### 4.3 Problem Identification — the hard part
This is the step you specifically flagged, and it deserves its own design because naive keyword matching will get it wrong often:

- Lectures often build up to a problem gradually (whiteboard explanation, then code). The LLM needs to find the *problem statement moment*, not just topic mentions.
- Many DSA problems have near-duplicate variants (Single Number I/II/III, Majority Element I/II, Subarray Sum variants). Getting the exact variant right is the whole point of your ask.
- **Approach:** LLM Pass #2 is prompted specifically to extract a *problem description* (inputs, outputs, constraints, the core trick used) — not just "what topic." That description is then matched against your curated DB by tags + a short semantic similarity check on the description text (cheap even without a full vector DB — you can do this with a handful of embedding calls per lecture, it's not high volume).
- **Human-in-the-loop confirmation is non-negotiable for MVP.** Show top 3 candidate matches with reasoning ("this matches because both use XOR cancellation on duplicates"), you pick one, it's saved forever against that lecture. This turns your matching accuracy problem into a one-time cost instead of a recurring one — by lecture 48 you'll have almost no unmatched problems left, and new lectures will mostly auto-match against patterns you've already confirmed.

### 4.4 Curated Problem Database
Don't let the LLM invent problems. Build a JSON/SQLite table you control:

```json
{
  "id": "lc-169",
  "title": "Majority Element",
  "platform": "LeetCode",
  "url": "https://leetcode.com/problems/majority-element/",
  "difficulty": "Easy",
  "patterns": ["Boyer-Moore", "HashMap", "Array"],
  "related_variants": ["lc-229"],
  "prerequisites": ["Hashing", "Array"]
}
```

Start with ~100–150 problems covering the patterns Scaler's DSA course actually teaches (arrays, two pointers, sliding window, bit manipulation, recursion/backtracking, trees, graphs, DP, greedy). This is a real chunk of manual work — budget a couple of evenings for it — but it's what makes recommendations trustworthy instead of hallucinated.

### 4.5 Recommendation Engine
Given a confirmed problem + its pattern tags:
- Pull all DB problems sharing ≥1 tag
- Exclude problems already logged as solved
- Order: 2 Easy → 2 Medium → 1 Hard (tunable), skipping tiers you've already logged as "too easy" recently (this is where the feedback loop from 4.7 plugs in)

### 4.6 Revision Engine (Spaced Repetition)
Rather than a vague "revise old topics" nudge, use a real scheduling algorithm — **SM-2** (the algorithm behind Anki) is a good fit and simple to implement:
- Each *pattern* (not each problem) has a review interval that grows if you keep succeeding on it, and shrinks if you struggle
- Inputs per attempt: solved? (y/n), self-rated difficulty (1–5), time taken, hint used?
- Output: a due-today list of patterns to re-test, each pointing to one unsolved problem from that pattern in your DB
- This becomes a genuinely separate daily view: "Today's new lecture sheet" + "Today's revision due"

### 4.7 Feedback Loop
Every solve attempt writes a row:
```json
{"problem_id": "lc-169", "solved": true, "difficulty_felt": "Easy", "time_min": 18, "used_hint": false, "date": "2026-08-04"}
```
This feeds both the recommendation engine (don't keep suggesting Easy in a pattern you've clearly got) and the revision engine (SM-2 interval calculation).

---

## 5. Data Models Summary

| Entity | Key fields |
|---|---|
| `Lecture` | id, video_path, transcript_path, date, topics[] |
| `Problem` | id, title, platform, url, difficulty, patterns[], prerequisites[] |
| `LectureProblemMatch` | lecture_id, problem_id, confirmed_by_user, timestamp_in_video |
| `Attempt` | problem_id, solved, difficulty_felt, time_min, used_hint, date |
| `RevisionSchedule` | pattern, next_due_date, interval, ease_factor (SM-2 state) |

SQLite is genuinely enough here — this is single-user, low volume. No need for Postgres unless you later turn this into a multi-user product.

---

## 6. Tech Stack (MVP-appropriate, not aspirational)

| Layer | Choice | Why |
|---|---|---|
| Transcription | `faster-whisper` (local) | No per-lecture API cost across 48+ lectures; runs offline |
| Concept/problem extraction | Claude or GPT via API | Structured JSON output prompts |
| Matching | Tag overlap + optional embedding sim | No vector DB needed yet |
| Storage | SQLite | Single user, simple, zero ops |
| Interface | CLI first → Streamlit later | Iterate on logic before building UI |
| Scheduler for revision | SM-2, implemented directly (~50 lines) | Well-documented, no library needed |

Skip FastAPI/Next.js/ChromaDB/Postgres for now — they're the right stack for *productionizing* this later, not for proving it works on your own 48 lectures.

---

## 7. Build Phases

1. **Phase 0** — Transcribe all 48 lectures, store transcripts. One-time batch job.
2. **Phase 1** — Concept extraction prompt, run on 3–4 lectures, manually sanity-check output.
3. **Phase 2** — Build curated Problem DB (~100–150 entries) for the patterns your lectures actually cover.
4. **Phase 3** — Problem identification + matching + your confirmation UI (can literally be a CLI prompt: "Is this LeetCode 169? [y/n/show more]").
5. **Phase 4** — Recommendation engine, ordered output per lecture.
6. **Phase 5** — Attempt logging + SM-2 revision scheduler.
7. **Phase 6** — Run the full pipeline on all 48 lectures, backfill your practice sheets.
8. **Phase 7** (optional, later) — Embedding-based matching, Streamlit UI, auto-ingest new lectures as they arrive weekly.

Each phase is independently useful — you get value after Phase 4 already, without needing revision or embeddings.

---

## 8. Open Questions / Risks

- **Whisper accuracy on technical terms:** DSA jargon ("Boyer-Moore", "XOR", variable names) may get mis-transcribed. Worth spot-checking a few transcripts before trusting the pipeline; a custom vocabulary/prompt hint to Whisper can help.
- **Ambiguous lectures:** Some lectures may cover a technique without solving one clean canonical problem (e.g. a concept-building lecture). Your confirmation step needs a "no clean match, skip this lecture" option.
- **DB coverage:** if a lecture covers a problem not in your curated 150, you'll need a lightweight "add new problem to DB" flow rather than letting the LLM guess.

---

## 9. Suggested Repo Structure

```
dsa-tool/
├── data/
│   ├── lectures/            # transcripts, metadata
│   ├── problems.json        # curated problem DB
│   ├── matches.db           # SQLite: lecture-problem matches
│   └── attempts.db          # SQLite: solve logs
├── pipeline/
│   ├── transcribe.py
│   ├── extract_concepts.py
│   ├── identify_problem.py
│   ├── match_db.py
│   └── recommend.py
├── revision/
│   └── sm2_scheduler.py
├── cli.py                   # daily entrypoint: new sheet + revision due
└── prompts/
    ├── concept_extraction.txt
    └── problem_identification.txt
```

---

## Next Steps

If this structure works for you, the next concrete deliverables I can produce are:
1. The actual concept-extraction and problem-identification prompts (ready to paste into an API call)
2. The starter `problems.json` seeded with ~100 core DSA patterns
3. The SM-2 scheduler implementation
