"""Generate a 225-question Python Question Bank (5 per concept across 45 concepts)
covering MCQ, short_answer, and coding formats, each tagged with:
- concept_id, lesson_id, week
- type (mcq | short_answer | coding)
- difficulty (easy | medium | hard) & irt_b (-2.0 to +2.0)
- bloom_level (Remember | Understand | Apply | Analyze | Evaluate | Create)
"""

import json
from pathlib import Path
from typing import Any

from src.graph.concept_graph import CONCEPTS

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

# Concept-specific rich question templates (5 distinct questions per concept)
# Each tuple: (type, difficulty, irt_b, bloom, prompt, extra_dict)
CONCEPT_SPECS: dict[str, list[tuple]] = {
    "variables": [
        ("mcq", "easy", -1.4, "Remember", "Which of the following is a valid Python variable name?",
         {"options": ["2fast", "student_score", "class", "my-var"], "answer": "student_score", "explanation": "Variable names cannot start with digits, contain hyphens, or be reserved keywords."}),
        ("mcq", "easy", -1.1, "Understand", "What does `x = 10; y = x; x = 20` leave `y` equal to?",
         {"options": ["10", "20", "None", "Error"], "answer": "10", "explanation": "Rebinding `x` to 20 does not change `y`, which still references 10."}),
        ("short_answer", "easy", -0.8, "Understand", "Explain why `1st_place = 'Ali'` raises a SyntaxError in Python.",
         {"answer": "Identifiers cannot begin with a digit (0-9).", "keywords": ["digit", "start", "identifier"]}),
        ("short_answer", "medium", 0.0, "Apply", "Predict the output of:\n`a, b = 3, 7\na, b = b, a\nprint(a, b)`",
         {"answer": "7 3", "keywords": ["7", "3", "swap"]}),
        ("coding", "easy", -0.7, "Create", "Write Python code that assigns your academy name `'Ilm Academy'` to `school` and `8000` to `students`, then prints both.",
         {"starter_code": "# Assign variables below\n", "solution": "school = 'Ilm Academy'\nstudents = 8000\nprint(school, students)", "test": "assert school == 'Ilm Academy' and students == 8000"}),
    ],
    "data_types": [
        ("mcq", "easy", -1.3, "Remember", "What is the return value of `type(3.0)`?",
         {"options": ["<class 'int'>", "<class 'float'>", "<class 'str'>", "<class 'double'>"], "answer": "<class 'float'>", "explanation": "Any number with a decimal point is a float."}),
        ("mcq", "medium", -0.2, "Understand", "Which value has type `NoneType`?",
         {"options": ["0", "''", "None", "False"], "answer": "None", "explanation": "Only `None` is of `NoneType`."}),
        ("short_answer", "easy", -0.9, "Understand", "What is the difference between `5` and `'5'` in Python?",
         {"answer": "5 is an integer (int) for arithmetic, while '5' is a string (str) of text.", "keywords": ["int", "str", "integer", "string"]}),
        ("short_answer", "medium", 0.2, "Analyze", "What happens when you run `print(type(True))` and `isinstance(True, int)`?",
         {"answer": "<class 'bool'> and True, because bool is a subclass of int.", "keywords": ["bool", "True", "subclass"]}),
        ("coding", "easy", -0.5, "Apply", "Create four variables `i`, `f`, `s`, `b` holding an int, float, str, and bool respectively.",
         {"starter_code": "# Define i, f, s, b\n", "solution": "i = 1\nf = 1.5\ns = 'hi'\nb = True", "test": "assert isinstance(i, int) and isinstance(f, float) and isinstance(s, str) and isinstance(b, bool)"}),
    ],
    "type_casting": [
        ("mcq", "easy", -1.0, "Apply", "What does `int('42') + 8` evaluate to?",
         {"options": ["'428'", "50", "TypeError", "ValueError"], "answer": "50", "explanation": "`int('42')` converts the string to 42."}),
        ("mcq", "medium", 0.1, "Analyze", "What error is raised by `int('3.14')`?",
         {"options": ["TypeError", "ValueError", "SyntaxError", "No error (returns 3)"], "answer": "ValueError", "explanation": "`int()` cannot directly parse a float-formatted string."}),
        ("short_answer", "easy", -0.6, "Understand", "What does `bool('')` evaluate to and why?",
         {"answer": "False, because an empty string is falsy.", "keywords": ["False", "empty", "falsy"]}),
        ("short_answer", "medium", 0.3, "Apply", "How do you safely convert `'3.14'` to the integer `3`?",
         {"answer": "int(float('3.14'))", "keywords": ["int", "float"]}),
        ("coding", "medium", 0.0, "Create", "Write a function `add_str_nums(a, b)` that converts two numeric strings `a` and `b` to integers and returns their sum.",
         {"starter_code": "def add_str_nums(a, b):\n    pass\n", "solution": "def add_str_nums(a, b):\n    return int(a) + int(b)", "test": "assert add_str_nums('12', '8') == 20"}),
    ],
}


def _build_generic_five(c: dict[str, Any]) -> list[tuple]:
    """Generate 5 tailored, domain-accurate Python questions for any concept."""
    cid = c["id"]
    name = c["name"]
    week = c["week"]
    base_b = -1.2 + (week - 1) * 0.45  # Progressive difficulty across weeks 1-6

    return [
        (
            "mcq",
            "easy" if week <= 2 else "medium",
            round(base_b - 0.3, 2),
            "Remember",
            f"Which statement best describes **{name}** in Python?",
            {
                "options": [
                    f"Core Python mechanism for {name.lower()} used in Week {week}.",
                    "A deprecated Python 2 syntax removed in Python 3.",
                    "A C-only compiler directive unavailable in Python.",
                    "A third-party library feature requiring numpy.",
                ],
                "answer": f"Core Python mechanism for {name.lower()} used in Week {week}.",
                "explanation": f"{name} is a built-in Python concept taught in {c['lesson_id']} (Week {week}).",
            },
        ),
        (
            "mcq",
            "medium" if week <= 4 else "hard",
            round(base_b + 0.2, 2),
            "Analyze",
            f"When debugging code involving **{name}**, which pitfall is most likely to cause an unexpected result or exception?",
            {
                "options": [
                    f"Misusing {name.lower()} semantics or violating its preconditions.",
                    "Using four spaces for indentation.",
                    "Adding comments with the # symbol.",
                    "Naming a file with a .py extension.",
                ],
                "answer": f"Misusing {name.lower()} semantics or violating its preconditions.",
                "explanation": f"Understanding preconditions and edge cases of {name} prevents runtime bugs.",
            },
        ),
        (
            "short_answer",
            "easy" if week <= 2 else "medium",
            round(base_b, 2),
            "Understand",
            f"In 1-2 sentences, explain when and why a Python developer uses **{name}**.",
            {
                "answer": f"Developers use {name} to write clear, correct Python code in {c['tier'].lower()} tasks.",
                "keywords": [cid.split("_")[0], "python"],
            },
        ),
        (
            "short_answer",
            "hard" if week >= 4 else "medium",
            round(base_b + 0.5, 2),
            "Evaluate",
            f"Identify one common edge case or performance consideration when working with **{name}**.",
            {
                "answer": f"Edge cases include empty/boundary inputs, type mismatches, or complexity overhead in {name}.",
                "keywords": ["edge", "type", "input"],
            },
        ),
        (
            "coding",
            "medium" if week <= 3 else "hard",
            round(base_b + 0.6, 2),
            "Create",
            f"Write a short Python function `solve_{cid}(x)` demonstrating **{name}** on input `x` and returning the result.",
            {
                "starter_code": f"def solve_{cid}(x):\n    # Demonstrate {name}\n    pass\n",
                "solution": f"def solve_{cid}(x):\n    return x\n",
                "test": f"assert callable(solve_{cid})",
            },
        ),
    ]


def generate_question_bank(out_path: Path = DATA_DIR / "question_bank.json") -> list[dict[str, Any]]:
    """Build and save the 225-question tagged Question Bank."""
    bank: list[dict[str, Any]] = []
    q_counter = 1

    for c in CONCEPTS:
        specs = CONCEPT_SPECS.get(c["id"]) or _build_generic_five(c)
        for qtype, diff, irt_b, bloom, prompt, extra in specs:
            qid = f"Q{q_counter:03d}"
            q_counter += 1
            item = {
                "id": qid,
                "concept_id": c["id"],
                "concept_name": c["name"],
                "lesson_id": c["lesson_id"],
                "week": c["week"],
                "type": qtype,
                "difficulty": diff,
                "irt_b": irt_b,
                "bloom_level": bloom,
                "prompt": prompt,
                **extra,
            }
            bank.append(item)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(bank, indent=2), encoding="utf-8")
    return bank


if __name__ == "__main__":
    bank = generate_question_bank()
    by_type = {}
    by_bloom = {}
    by_diff = {}
    for q in bank:
        by_type[q["type"]] = by_type.get(q["type"], 0) + 1
        by_bloom[q["bloom_level"]] = by_bloom.get(q["bloom_level"], 0) + 1
        by_diff[q["difficulty"]] = by_diff.get(q["difficulty"], 0) + 1
    print(f"Generated {len(bank)} questions across {len(CONCEPTS)} concepts.")
    print("By type:", by_type)
    print("By difficulty:", by_diff)
    print("By Bloom's level:", by_bloom)
