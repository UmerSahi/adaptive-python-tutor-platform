"""Question Generation & Difficulty Calibration (Day 3, Tasks 4 & 5):
- Generates MCQs with misconception-based distractors, short answers, and coding questions with tests
- Validates every generated question (schema, distractor uniqueness, AST parse + unit-test execution)
- Reports acceptance rate
- Compares predicted difficulty with measured 2PL IRT difficulty (Pearson r, MAE) and retires weak questions
"""

import ast
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import pearsonr

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUTS_DIR = BASE_DIR / "outputs"


def generate_candidate_questions() -> list[dict[str, Any]]:
    """Generate a curated batch of 15 candidate questions (MCQs with misconception distractors, short answer, coding with tests)."""
    candidates = [
        # MCQs with misconception-based distractors
        {
            "id": "GEN_001", "concept_id": "recursion", "type": "mcq", "predicted_b": 0.8,
            "prompt": "What happens if a recursive function is missing its base case?",
            "options": [
                "It raises RecursionError after exceeding maximum recursion depth.",
                "Python automatically stops after 10 calls and returns None.",
                "It converts itself into a for loop at runtime.",
                "It returns 0 on the second call.",
            ],
            "distractor_misconceptions": [
                "Correct",
                "Assumes Python auto-terminates recursion",
                "Confuses recursion with tail-call loop optimization",
                "Assumes default numeric return",
            ],
            "answer": "It raises RecursionError after exceeding maximum recursion depth.",
        },
        {
            "id": "GEN_002", "concept_id": "mutability", "type": "mcq", "predicted_b": 0.4,
            "prompt": "Given `a = [1, 2]; b = a; b.append(3)`, what is `a`?",
            "options": ["[1, 2, 3]", "[1, 2]", "[3]", "TypeError"],
            "distractor_misconceptions": ["Correct", "Assumes b = a copies the list", "Confuses append with overwrite", "Assumes lists are immutable"],
            "answer": "[1, 2, 3]",
        },
        {
            "id": "GEN_003", "concept_id": "parameters_defaults", "type": "mcq", "predicted_b": 0.6,
            "prompt": "Why is `def add_item(x, items=[]):` considered a bug in Python?",
            "options": [
                "The default list is created once and shared across all calls.",
                "Default arguments cannot be lists in Python 3.",
                "It causes a SyntaxError unless typed.",
                "It resets `items` to None after the first call.",
            ],
            "distractor_misconceptions": ["Correct", "False syntax restriction", "False syntax rule", "Confuses None sentinel pattern"],
            "answer": "The default list is created once and shared across all calls.",
        },
        {
            "id": "GEN_004", "concept_id": "dictionaries", "type": "mcq", "predicted_b": -0.2,
            "prompt": "What does `{'a': 1}.get('b', 0)` return?",
            "options": ["0", "None", "KeyError", "'b'"],
            "distractor_misconceptions": ["Correct", "Forgets default argument to .get()", "Confuses .get() with [] indexing", "Confuses key with default value"],
            "answer": "0",
        },
        {
            "id": "GEN_005", "concept_id": "list_indexing_slicing", "type": "mcq", "predicted_b": -0.3,
            "prompt": "What is `[10, 20, 30, 40][1:3]`?",
            "options": ["[20, 30]", "[20, 30, 40]", "[10, 20, 30]", "[10, 20]"],
            "distractor_misconceptions": ["Correct", "Off-by-one: assumes stop index is inclusive", "Assumes 1-based indexing", "Confuses stop with length"],
            "answer": "[20, 30]",
        },
        # Short answer questions
        {
            "id": "GEN_006", "concept_id": "return_values", "type": "short_answer", "predicted_b": -0.1,
            "prompt": "If a function uses `print(x)` instead of `return x`, what value does `res = f(5)` hold?",
            "answer": "None",
            "rubric_keywords": ["none"],
        },
        {
            "id": "GEN_007", "concept_id": "hashing_concepts", "type": "short_answer", "predicted_b": 0.5,
            "prompt": "Why can a tuple `(1, 2)` be a dictionary key while a list `[1, 2]` cannot?",
            "answer": "Tuples are immutable and hashable, whereas lists are mutable and unhashable.",
            "rubric_keywords": ["immutable", "hashable", "mutable"],
        },
        {
            "id": "GEN_008", "concept_id": "context_managers", "type": "short_answer", "predicted_b": 0.2,
            "prompt": "What advantage does `with open('a.txt') as f:` have over `f = open('a.txt')`?",
            "answer": "It guarantees the file is closed automatically even if an exception occurs.",
            "rubric_keywords": ["close", "automatic", "exception"],
        },
        {
            "id": "GEN_009", "concept_id": "time_complexity", "type": "short_answer", "predicted_b": 1.0,
            "prompt": "Why is binary search O(log n) while linear search is O(n)?",
            "answer": "Binary search halves the sorted search space each step, whereas linear search checks elements one by one.",
            "rubric_keywords": ["halves", "sorted", "one by one"],
        },
        {
            "id": "GEN_010", "concept_id": "variable_scope", "type": "short_answer", "predicted_b": 0.4,
            "prompt": "What do the four letters in Python's LEGB scope rule stand for?",
            "answer": "Local, Enclosing, Global, Built-in",
            "rubric_keywords": ["local", "enclosing", "global", "built-in"],
        },
        # Coding questions with executable unit tests
        {
            "id": "GEN_011", "concept_id": "recursion", "type": "coding", "predicted_b": 0.9,
            "prompt": "Write a recursive function `factorial(n)` that returns n! for n >= 0.",
            "solution": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)\n",
            "tests": "assert factorial(0) == 1\nassert factorial(5) == 120",
        },
        {
            "id": "GEN_012", "concept_id": "list_comprehensions", "type": "coding", "predicted_b": 0.3,
            "prompt": "Write `even_squares(nums)` returning squares of even numbers using a list comprehension.",
            "solution": "def even_squares(nums):\n    return [x * x for x in nums if x % 2 == 0]\n",
            "tests": "assert even_squares([1, 2, 3, 4]) == [4, 16]\nassert even_squares([1, 3]) == []",
        },
        {
            "id": "GEN_013", "concept_id": "dictionaries", "type": "coding", "predicted_b": 0.2,
            "prompt": "Write `char_freq(s)` returning a dictionary of character frequencies in string `s`.",
            "solution": "def char_freq(s):\n    counts = {}\n    for ch in s:\n        counts[ch] = counts.get(ch, 0) + 1\n    return counts\n",
            "tests": "assert char_freq('aba') == {'a': 2, 'b': 1}\nassert char_freq('') == {}",
        },
        {
            "id": "GEN_014", "concept_id": "exceptions_try_except", "type": "coding", "predicted_b": 0.4,
            "prompt": "Write `safe_div(a, b)` returning `a / b`, or `None` if `b == 0`.",
            "solution": "def safe_div(a, b):\n    try:\n        return a / b\n    except ZeroDivisionError:\n        return None\n",
            "tests": "assert safe_div(10, 2) == 5.0\nassert safe_div(5, 0) is None",
        },
        # Intentionally flawed candidate to verify validator catches & rejects bad questions
        {
            "id": "GEN_015", "concept_id": "for_loops", "type": "coding", "predicted_b": 0.1,
            "prompt": "Write `sum_list(nums)` returning the sum of `nums`.",
            "solution": "def sum_list(nums):\n    return sum(nums) + 1  # intentional off-by-one bug\n",
            "tests": "assert sum_list([1, 2, 3]) == 6",
        },
    ]
    return candidates


def validate_question(q: dict[str, Any]) -> tuple[bool, str]:
    """Validate schema, distractor quality, and executable Python tests."""
    if not q.get("prompt") or not q.get("concept_id"):
        return False, "Missing prompt or concept_id"
    if q["type"] == "mcq":
        opts = q.get("options", [])
        if len(opts) != 4 or len(set(opts)) != 4:
            return False, "MCQ must have 4 unique options"
        if q.get("answer") not in opts:
            return False, "Answer not in options"
    elif q["type"] == "short_answer":
        if not q.get("answer") or not q.get("rubric_keywords"):
            return False, "Short answer missing answer or rubric_keywords"
    elif q["type"] == "coding":
        try:
            ast.parse(q["solution"])
            ast.parse(q["tests"])
            ns: dict[str, Any] = {}
            exec(compile(q["solution"] + "\n" + q["tests"], q["id"], "exec"), ns)
        except Exception as exc:
            return False, f"Coding test failed: {type(exc).__name__}: {exc}"
    return True, "OK"


def run_generation_and_calibration():
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    candidates = generate_candidate_questions()
    accepted = []
    rejected = []

    for q in candidates:
        ok, reason = validate_question(q)
        q["validation_status"] = "accepted" if ok else "rejected"
        q["validation_reason"] = reason
        if ok:
            accepted.append(q)
        else:
            rejected.append(q)

    acc_rate = len(accepted) / len(candidates)
    (OUTPUTS_DIR / "generated_questions.json").write_text(
        json.dumps(candidates, indent=2), encoding="utf-8"
    )
    print(f"Generated: {len(candidates)} | Accepted: {len(accepted)} | Rejected: {len(rejected)} | Acceptance Rate: {acc_rate:.1%}")

    # Difficulty calibration: compare predicted (authored) irt_b vs measured 2PL IRT b
    qbank = json.loads((DATA_DIR / "question_bank.json").read_text(encoding="utf-8"))
    qbank_df = pd.DataFrame(qbank)[["id", "concept_id", "type", "difficulty", "irt_b"]].rename(
        columns={"id": "question_id", "irt_b": "predicted_b"}
    )
    irt_path = OUTPUTS_DIR / "irt_question_params.csv"
    if irt_path.exists():
        irt_df = pd.read_csv(irt_path)
        cal_df = qbank_df.merge(irt_df, on="question_id", how="inner")
        r_val, p_val = pearsonr(cal_df["predicted_b"], cal_df["irt_b"])
        mae = float(np.mean(np.abs(cal_df["predicted_b"] - cal_df["irt_b"])))
        cal_df["retired"] = (cal_df["irt_a"] < 0.45) | (cal_df["irt_b"].abs() > 2.2)
        retired_cnt = int(cal_df["retired"].sum())
        cal_df.to_csv(OUTPUTS_DIR / "difficulty_calibration.csv", index=False)
        print(
            f"Difficulty Calibration (n={len(cal_df)}): Pearson r={r_val:.4f} (p={p_val:.2e}), "
            f"MAE={mae:.4f} | Retired weak questions: {retired_cnt}"
        )


if __name__ == "__main__":
    run_generation_and_calibration()
