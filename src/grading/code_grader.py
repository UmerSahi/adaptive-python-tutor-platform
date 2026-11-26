"""Test-Based Code Auto-Grader & AI Code Feedback (Day 4, Tasks 2 & 3):
- Visible + hidden test cases, partial marks, timeouts, efficiency check
- Compares auto-grader marks with simulated teacher marks across 50 submissions
- Generates structured code feedback: failed test explanations, AST quality/McCabe complexity,
  one concrete improvement, and lesson link (never gives full solution)
"""

import ast
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import pearsonr

from src.grading.sandbox import run_in_sandbox

BASE_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUTS_DIR = BASE_DIR / "outputs"


def _mccabe_complexity(code: str) -> int:
    """Compute approximate McCabe cyclomatic complexity via AST."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return 1
    complexity = 1
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler, ast.With, ast.IfExp)):
            complexity += 1
        elif isinstance(node, ast.BoolOp):
            complexity += len(node.values) - 1
    return complexity


def analyze_code_quality(code: str) -> dict[str, Any]:
    """Ruff/Pylint/Radon-style static quality metrics via AST."""
    lines = [ln for ln in code.splitlines() if ln.strip()]
    complexity = _mccabe_complexity(code)
    issues = []
    if len(lines) > 0 and max(len(ln) for ln in lines) > 100:
        issues.append("Line exceeds 100 chars (PEP 8).")
    if complexity > 5:
        issues.append(f"High cyclomatic complexity ({complexity}); consider simplifying branches.")
    if "print(" in code and "return" not in code:
        issues.append("Uses print() without return; functions should return values.")
    return {
        "loc": len(lines),
        "cyclomatic_complexity": complexity,
        "quality_issues": issues,
    }


def grade_submission(
    code: str,
    visible_tests: list[str],
    hidden_tests: list[str],
    lesson_id: str = "L06",
    max_ms_budget: float = 1200.0,
) -> dict[str, Any]:
    """Run visible & hidden tests in sandbox, score partial marks, check efficiency, and generate feedback."""
    all_tests = [("visible", t) for t in visible_tests] + [("hidden", t) for t in hidden_tests]
    passed_count = 0
    failed_explanations = []
    total_ms = 0.0

    for vis, test_stmt in all_tests:
        harness = f"{code}\n{test_stmt}"
        res = run_in_sandbox(harness, timeout_sec=2.0)
        total_ms += res["elapsed_ms"]
        if res["passed"]:
            passed_count += 1
        else:
            label = f"Visible test `{test_stmt}`" if vis == "visible" else "Hidden edge-case test"
            err_msg = res["stderr"].strip().splitlines()[-1] if res["stderr"].strip() else res["status"]
            failed_explanations.append(f"{label} failed ({err_msg}).")

    score_pct = round(100.0 * passed_count / max(1, len(all_tests)), 1)
    efficient = total_ms <= max_ms_budget
    quality = analyze_code_quality(code)

    # One targeted improvement + lesson link (never gives full solution)
    if failed_explanations:
        improvement = (
            "Check your base/boundary condition for edge-case inputs (e.g., 0, empty list, or negative values)."
        )
    elif not efficient:
        improvement = "Your solution passes tests but runs slowly; look for redundant nested loops."
    elif quality["quality_issues"]:
        improvement = quality["quality_issues"][0]
    else:
        improvement = "Clean solution! Add a concise docstring describing parameters and return value."

    return {
        "score_pct": score_pct,
        "passed_tests": passed_count,
        "total_tests": len(all_tests),
        "total_elapsed_ms": round(total_ms, 2),
        "efficiency_ok": efficient,
        "quality": quality,
        "failed_tests_explained": failed_explanations,
        "one_improvement": improvement,
        "lesson_link": f"[Lesson {lesson_id} Reference]",
    }


def run_50_submission_benchmark():
    """Grade 50 diverse Python submissions and compare against simulated teacher marks."""
    visible = ["assert factorial(0) == 1", "assert factorial(3) == 6"]
    hidden = ["assert factorial(5) == 120", "assert factorial(1) == 1"]

    variants = [
        ("def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)", 100.0),
        ("def factorial(n):\n    if n == 0:\n        return 1\n    res = 1\n    for i in range(1, n + 1):\n        res *= i\n    return res", 100.0),
        ("def factorial(n):\n    if n == 1:\n        return 1\n    return n * factorial(n - 1)", 25.0),  # misses 0!
        ("def factorial(n):\n    return n * factorial(n - 1)", 0.0),  # infinite recursion
        ("def factorial(n):\n    return 1 if n <= 1 else 6 if n == 3 else 0", 75.0),  # hardcodes 3
    ]

    rng = np.random.default_rng(42)
    rows = []
    sample_feedback = []

    for i in range(50):
        code, base_teacher = variants[i % len(variants)]
        # Teacher mark has realistic +/- 5 pt human rubric variance
        teacher_mark = float(np.clip(base_teacher + rng.normal(0, 4.0), 0.0, 100.0))
        res = grade_submission(code, visible, hidden, lesson_id="L06")
        rows.append(
            {
                "submission_id": f"SUB_{i+1:03d}",
                "auto_score": res["score_pct"],
                "teacher_score": round(teacher_mark, 1),
                "abs_diff": round(abs(res["score_pct"] - teacher_mark), 1),
                "elapsed_ms": res["total_elapsed_ms"],
            }
        )
        if i < 5:
            sample_feedback.append({"submission_id": f"SUB_{i+1:03d}", **res})

    df = pd.DataFrame(rows)
    r_val, _ = pearsonr(df["auto_score"], df["teacher_score"])
    mae = df["abs_diff"].mean()
    within_10 = (df["abs_diff"] <= 10.0).mean()

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUTS_DIR / "grading_teacher_comparison.csv", index=False)
    (OUTPUTS_DIR / "grading_feedback_samples.json").write_text(
        json.dumps(sample_feedback, indent=2), encoding="utf-8"
    )
    print(f"Graded 50 submissions | Pearson r={r_val:.4f} | MAE={mae:.2f} pts | Within 10 pts: {within_10:.1%}")
    return df


if __name__ == "__main__":
    run_50_submission_benchmark()
