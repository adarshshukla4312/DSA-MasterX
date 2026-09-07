"""
Full Scaler Academy — Java DSA Curriculum (113 Videos)
Includes layered pedagogical classification and learning objective metadata.
"""

FULL_CURRICULUM = [
    "1. Meet and Greet",
    "2. Dare to Dream",
    "3. High Level Design - Basics",
    "4. Low Level Design - Basics",
    "5. Beginner _ Logical Thinking - 1",
    "6. Beginner _ Logical Thinking - 2",
    "7. Beginner _ Java Basics - 1",
    "8. Beginner _ Java Basics - 2",
    "9. Beginner _ Pattern Problems",
    "10. Beginner _ Functions",
    "11. Beginner _ Arrays",
    "12. Beginner Java _ 1D and 2D Arrays",
    "13. Java Memory Management",
    "14. Beginner _ 1D and 2D Arraylists",
    "15. Beginner _ Strings",
    "16. Beginner _ OOPS",
    "17. Beginner _ Maths",
    "18. Intermediate DSA _ Introduction to Problem Solving",
    "19. Intermediate DSA _ Time Complexity - 1",
    "20. Intermediate DSA _ Time Complexity - 2",
    "21. Intermediate DSA _ Introduction to Arrays",
    "22. Intermediate DSA _ Arrays - Prefix Sum",
    "23. Intermediate DSA _ Arrays _ Subarrays",
    "24. Intermediate DSA _ Arrays _ 2D Matrices",
    "25. Intermediate DSA _ Arrays _ Interview Problems",
    "26. Intermediate DSA _ Bit Manipulations - 1",
    "27. Intermediate DSA _ Bit Manipulations - 2",
    "28. Intermediate DSA _ Bit Manipulation 3",
    "29. Intermediate DSA _ Maths _ Modular Arithmetic Introduction",
    "30. Intermediate DSA _ Arrays & Maths",
    "31. Intermediate DSA _ Sorting",
    "32. Intermediate DSA _ Strings",
    "33. Intermediate DSA _ Additional Problems _ Arrays, Strings and Sorting",
    "34. Intermediate DSA _ Hashing - 1",
    "35. Intermediate DSA _ Hashing - 2",
    "36. Intermediate DSA _ Recursion - 1",
    "37. Intermediate DSA _ Recursion - 2",
    "38. Dare to Dream",
    "39. Intermediate DSA _ Linked List Basics",
    "40. Intermediate DSA _ Recursion - 3",
    "41. Intermediate DSA _ Stacks and Queues - Basics",
    "42. Intermediate DSA _ Trees Basics - 1",
    "43. Intermediate DSA _ Trees Basics - 2",
    "44. Academy Intermediate DSA _ Contest 2 Discussion Class",
    "45. Advanced DSA _ Arrays - 1",
    "46. Advanced DSA _ Arrays - 2",
    "47. Advanced DSA _ Arrays - 3",
    "48. Advanced DSA _ Bit Manipulations - 1",
    "49. Advanced DSA _ Bit Manipulations - 2",
    "50. Advanced DSA _ Maths - Modular Arithmetic",
    "51. Advanced DSA _ Maths - GCD",
    "52. DSA _ Maths - Prime Numbers",
    "53. Advanced DSA _ Maths - Combinatorics",
    "54. Advanced DSA _ Recursion - 1",
    "55. Advanced DSA _ Recursion - 2",
    "56. Advanced DSA _ Sorting - 1",
    "57. Advanced DSA _ Sorting - 2",
    "58. Advanced DSA _ Sorting - 3",
    "59. Advanced DSA _ Binary Search - 1",
    "60. Advanced DSA _ Binary Search - 2",
    "61. Advanced DSA _ Binary Search - 3",
    "62. Advanced DSA _ Binary Search - 4",
    "63. Advanced DSA _ Two Pointers - 1",
    "64. Advanced DSA _ Hashing - 1",
    "65. Advanced DSA _ Hashing - 2",
    "66. Advanced DSA _ Strings Pattern Matching",
    "67. Advanced DSA _ Problems on Strings with Hashmaps",
    "68. Advanced DSA _ Linked List - 1",
    "69. Advanced DSA _ Hashing 3",
    "70. Advanced DSA _ Linked List - 2",
    "71. Advanced DSA _ Linked List - 3",
    "72. Advanced DSA _ Stacks - 1",
    "73. Advanced DSA _ Stacks - 2",
    "74. Advanced DSA _ Queues - 1",
    "75. Advanced DSA _ Queue and Deque - 2",
    "76. Advanced DSA _ Trees 1 _ Structure of Binary Tree & Tree Traversals",
    "77. Advanced DSA _ Trees 2 _ Views & Types of Binary Tree",
    "78. Advanced DSA _ Tree 3 - Binary Search Tree",
    "79. Advanced DSA _ Trees 4 - Lowest Common Ancestor",
    "80. Advanced DSA _ Trees 5 - Problems on Trees",
    "81. Advanced DSA _ Trees 6 - Problems on Trees 2",
    "82. Advanced DSA _ Tries - 1",
    "83. Advanced DSA _ Tries - 2",
    "84. Advanced DSA _ Heaps - 1",
    "85. Advanced DSA _ Heaps - 2",
    "86. Advanced DSA _ Greedy Algorithms",
    "87. Advanced DSA _ Backtracking - 1",
    "88. Advanced DSA _ Backtracking - 2",
    "89. Advanced DSA _ Dynamic Programming - 1",
    "90. Advanced DSA _ Dynamic Programming - 2",
    "91. Advanced DSA _ Dynamic Programming - 3",
    "92. Advanced DSA _ Dynamic Programming - 4",
    "93. Advanced DSA _ Dynamic Programming - 5",
    "94. Advanced DSA _ Dynamic Programming - 6",
    "95. Advanced DSA _ Dynamic Programming - 7",
    "96. Advanced DSA _ Graphs - 1",
    "97. Advanced DSA _ Graphs - 2",
    "98. Advanced DSA _ Backtracking 3",
    "99. Advanced DSA _ Graphs - 3",
    "100. Advanced DSA _ Graphs - 4",
    "101. Advanced DSA _ Graphs - 5",
    "102. Language Module Townhall",
    "103. CS_ DBMS 1_ Intro to DBMS and Relational Model",
    "104. CS_ DBMS 4_ CRUD",
    "105. CS_ DBMS_ CRUD-2",
    "106. CS_ DBMS 5_ Joins",
    "107. CS_ DBMS 6_ Aggregation and Built-In Functions",
    "108. CS_ DBMS 7_ Transactions",
    "109. CS_ DBMS 8",
    "110. CS_ DBMS 9",
    "111. CS_ DBMS 10",
    "112. CS_ OS1",
    "113. CS_ OS2",
]

# ─── Pedagogical Layer Classification ─────────────────────────────────────────

LAYER_RANGES = {
    "beginner":     (1, 17),
    "intermediate": (18, 44),
    "advanced":     (45, 101),
    "cs_fundamentals": (102, 113),
}

LAYER_PHILOSOPHY = {
    "beginner": {
        "name": "Beginner — Programming Foundations",
        "cognitive_goal": "Programming Competence",
        "learning_question": "Can I implement this correctly?",
        "focus": (
            "The student is building programming proficiency. They need to master syntax, "
            "control flow, and basic data structures. Algorithmic optimization is NOT the concern yet. "
            "Focus on correctness, readability, and translating logical ideas into working code."
        ),
        "mcq_style": (
            "Test implementation knowledge: What does this code output? What happens if we change X? "
            "Which data structure stores elements in insertion order? Focus on language mechanics and basic correctness."
        ),
        "ladder_style": (
            "Problems should test whether the student can correctly implement the taught concept. "
            "Keep problems straightforward — direct application, no tricks. "
            "Emphasize getting the right output over optimizing time complexity."
        ),
    },
    "intermediate": {
        "name": "Intermediate — Algorithmic Foundations",
        "cognitive_goal": "Algorithmic Understanding & Pattern Recognition",
        "learning_question": "Under what circumstances should this algorithm be applied?",
        "focus": (
            "The student is learning WHY particular techniques work and WHEN to apply them. "
            "They should begin recognizing recurring computational patterns (prefix sum for range queries, "
            "hashing for lookups, recursion for self-similar subproblems). "
            "The shift is from 'how to code it' to 'why this approach works here'."
        ),
        "mcq_style": (
            "Test conceptual understanding and technique selection: What is the time complexity? "
            "Which approach is most efficient for this constraint? Why does prefix sum reduce repeated computation? "
            "What invariant does this algorithm maintain? Focus on the 'why' behind the technique."
        ),
        "ladder_style": (
            "Problems should progress from direct technique application to recognizing WHEN to apply it. "
            "Include problems where the student must CHOOSE the right technique (not just execute a given one). "
            "Avoid multi-concept synthesis — stick to single-technique problems with increasing edge-case complexity."
        ),
    },
    "advanced": {
        "name": "Advanced — Problem Solving & Algorithmic Reasoning",
        "cognitive_goal": "Pattern Recognition, Algorithm Selection & Multi-Concept Problem Solving",
        "learning_question": "Can I analyze an unfamiliar problem and determine the right combination of techniques?",
        "focus": (
            "The student is revisiting concepts they already know at a fundamentally deeper level. "
            "This is NOT about learning new algorithms — it's about developing the reasoning to COMBINE techniques, "
            "recognize non-obvious patterns, optimize solutions, and solve problems they've never seen before. "
            "The same topic (e.g., Arrays) now involves multi-step reasoning, clever observations, and synthesis."
        ),
        "mcq_style": (
            "Test algorithmic reasoning and optimization intuition: Why is approach A better than B for this constraint? "
            "What happens to the time complexity if we add this optimization? Which combination of techniques solves this? "
            "What is the key observation that reduces this from O(N^2) to O(N log N)? "
            "Focus on trade-offs, edge cases, and the reasoning behind choosing one approach over another."
        ),
        "ladder_style": (
            "Problems should require the student to COMBINE multiple techniques learned across earlier lectures. "
            "Include problems where the optimal approach is non-obvious and requires a key insight or observation. "
            "Progress toward problems where algorithm selection itself is the challenge — "
            "the student must figure out which tools from their toolkit apply."
        ),
    },
    "cs_fundamentals": {
        "name": "CS Fundamentals — DBMS & OS",
        "cognitive_goal": "Foundational CS Knowledge for Interviews",
        "learning_question": "Do I understand core CS concepts commonly asked in interviews?",
        "focus": "Foundational exposure to DBMS and OS concepts for interview preparation.",
        "mcq_style": "Test conceptual knowledge of databases, transactions, OS scheduling, and memory management.",
        "ladder_style": "Not applicable — these are theory-focused lectures without algorithmic problem ladders.",
    },
}


def get_layer(lecture_num: int) -> str:
    """Returns the pedagogical layer for a given lecture number."""
    for layer, (start, end) in LAYER_RANGES.items():
        if start <= lecture_num <= end:
            return layer
    return "unknown"


def get_layer_philosophy(lecture_num: int) -> dict:
    """Returns the full pedagogical philosophy for a lecture's layer."""
    layer = get_layer(lecture_num)
    return LAYER_PHILOSOPHY.get(layer, LAYER_PHILOSOPHY["intermediate"])


def get_prior_coverage(lecture_num: int, topic_stem: str) -> list[str]:
    """
    Finds all EARLIER lectures that covered the same base topic.
    E.g., for Advanced DSA Arrays - 1 (Lecture 45), returns:
    ['11. Beginner _ Arrays', '21. Intermediate DSA _ Introduction to Arrays', ...]
    """
    # Normalize the topic stem for matching
    search_terms = []
    # Extract the core subject (e.g., "Arrays", "Recursion", "Hashing")
    for keyword in ["Arrays", "Recursion", "Hashing", "Sorting", "Strings", "Bit Manipulation",
                     "Maths", "Trees", "Linked List", "Stacks", "Queues", "Binary Search",
                     "Dynamic Programming", "Graphs", "Backtracking", "Heaps", "Tries",
                     "Greedy", "Two Pointers", "OOPS", "Functions"]:
        if keyword.lower() in topic_stem.lower():
            search_terms.append(keyword.lower())

    if not search_terms:
        return []

    prior = []
    for title in FULL_CURRICULUM[:lecture_num - 1]:
        title_lower = title.lower()
        for term in search_terms:
            if term in title_lower:
                prior.append(title)
                break

    return prior


def get_curriculum_context(current_num: int) -> dict:
    """
    Returns structured context for a given lecture number including
    pedagogical layer, scope boundaries, and prior topic coverage.
    """
    total = len(FULL_CURRICULUM)
    idx = current_num - 1

    if idx < 0 or idx >= total:
        return {
            "current_title": f"Lecture {current_num}",
            "previous_titles": [],
            "upcoming_titles": [],
            "upcoming_same_topic": [],
            "prior_same_topic": [],
            "total": total,
            "layer": "unknown",
            "philosophy": LAYER_PHILOSOPHY["intermediate"],
        }

    current_title = FULL_CURRICULUM[idx]

    # Extract topic stem
    raw = current_title.split(". ", 1)[1] if ". " in current_title else current_title
    topic_stem = raw
    for suffix in [" - 1", " - 2", " - 3", " - 4", " - 5", " - 6", " - 7", " 1", " 2", " 3"]:
        if topic_stem.endswith(suffix):
            topic_stem = topic_stem[: -len(suffix)].rstrip()
            break

    previous = FULL_CURRICULUM[:idx]
    upcoming = FULL_CURRICULUM[idx + 1: min(idx + 8, total)]

    # Find upcoming lectures sharing the same topic stem
    upcoming_same_topic = []
    for future_title in FULL_CURRICULUM[idx + 1:]:
        future_raw = future_title.split(". ", 1)[1] if ". " in future_title else future_title
        if future_raw.startswith(topic_stem):
            upcoming_same_topic.append(future_title)

    # Find prior lectures on the same core subject (cross-layer)
    prior_same_topic = get_prior_coverage(current_num, topic_stem)

    layer = get_layer(current_num)
    philosophy = get_layer_philosophy(current_num)

    return {
        "current_title": current_title,
        "topic_stem": topic_stem,
        "previous_titles": previous,
        "upcoming_titles": upcoming,
        "upcoming_same_topic": upcoming_same_topic,
        "prior_same_topic": prior_same_topic,
        "total": total,
        "layer": layer,
        "philosophy": philosophy,
    }


def build_llm_course_context(current_num: int) -> str:
    """Builds the full pedagogical context string for LLM prompts."""
    ctx = get_curriculum_context(current_num)
    phi = ctx["philosophy"]

    prev_recent = ctx["previous_titles"][-8:]
    prev_str = ", ".join(prev_recent) if prev_recent else "None (First Lecture)"
    upcoming_str = ", ".join(ctx["upcoming_titles"][:5]) if ctx["upcoming_titles"] else "None (Last Lecture)"

    lines = [
        f"## Curriculum Position",
        f"{ctx['current_title']} (Lecture {current_num} of {ctx['total']}) in the Scaler Academy Java DSA Curriculum.",
        f"Recent Previous Lectures: [{prev_str}]",
        f"Upcoming Lectures: [{upcoming_str}]",
        "",
        f"## Pedagogical Layer: {phi['name']}",
        f"Cognitive Goal: {phi['cognitive_goal']}",
        f"Core Learning Question: \"{phi['learning_question']}\"",
        f"",
        f"### Layer Context",
        f"{phi['focus']}",
    ]

    # Cross-layer prior coverage
    if ctx["prior_same_topic"]:
        lines.append("")
        lines.append("### Prior Coverage of This Topic (Earlier Layers)")
        lines.append("The student has already encountered this subject in earlier lectures:")
        for t in ctx["prior_same_topic"]:
            lines.append(f"  - {t}")
        lines.append(
            "Build upon what they already know. Do NOT re-test basics they mastered in earlier layers. "
            "Focus on the NEW depth and reasoning introduced in THIS lecture."
        )

    # Scope boundary for future lectures in same series
    if ctx["upcoming_same_topic"]:
        lines.append("")
        lines.append("### SCOPE BOUNDARY (Future Lectures in Same Series)")
        lines.append("The following lectures cover the SAME topic at a DEEPER level and have NOT been taught yet:")
        for t in ctx["upcoming_same_topic"]:
            lines.append(f"  - {t}")
        lines.append(
            "Do NOT suggest problems that require techniques from these future lectures. "
            "The concept ladder MUST be solvable using ONLY what was taught in THIS video and prior lectures."
        )

    # MCQ and Ladder generation guidance
    lines.append("")
    lines.append("### Generation Guidance for This Layer")
    lines.append(f"MCQ Style: {phi['mcq_style']}")
    lines.append(f"Concept Ladder Style: {phi['ladder_style']}")

    return "\n".join(lines)
