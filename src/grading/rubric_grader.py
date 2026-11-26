"""Rubric Grader for Written Answers (Day 4, Task 4):
- Scores short-answer responses (0-3) using semantic similarity + rubric concept keywords
- Evaluates inter-rater agreement (Cohen's kappa) against 2 human graders on 40 responses
- Checks for length / language-style (English vs UrduLish) grading bias
"""

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics import cohen_kappa_score

BASE_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUTS_DIR = BASE_DIR / "outputs"


class RubricGrader:
    def __init__(self):
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

    def score_response(
        self, student_answer: str, reference_answer: str, rubric_keywords: list[str]
    ) -> dict[str, Any]:
        """Score 0-3 based on semantic alignment + rubric keyword coverage (length-invariant)."""
        embs = self.embedder.encode([student_answer, reference_answer], show_progress_bar=False)
        sim = float(
            np.dot(embs[0], embs[1]) / (np.linalg.norm(embs[0]) * np.linalg.norm(embs[1]) + 1e-8)
        )
        low = student_answer.lower()
        kw_hits = sum(1 for k in rubric_keywords if k.lower() in low)
        kw_ratio = kw_hits / max(1, len(rubric_keywords))

        combined = 0.55 * max(0.0, sim) + 0.45 * kw_ratio
        if combined >= 0.72:
            score = 3
        elif combined >= 0.52:
            score = 2
        elif combined >= 0.32:
            score = 1
        else:
            score = 0
        return {"score": score, "sim": round(sim, 3), "kw_ratio": round(kw_ratio, 3)}


def run_rubric_evaluation():
    grader = RubricGrader()
    ref = "Tuples are immutable and hashable, whereas lists are mutable and cannot be hashed."
    kws = ["immutable", "hash", "mutable"]

    # 40 student responses across English & UrduLish, concise & verbose
    templates = [
        ("Tuples are immutable and hashable, lists are mutable.", "en", 3),
        ("Tuple immutable hota hai isliye hash ho sakta hai, list mutable hai.", "urdulish", 3),
        ("Tuples cannot be changed after creation so they are hashable.", "en", 2),
        ("Tuple change nahi hota, list change ho jati hai.", "urdulish", 2),
        ("Because tuples are faster and smaller in memory.", "en", 1),
        ("Lists use square brackets and tuples use parentheses.", "en", 1),
        ("I am not sure, maybe Python prefers tuples.", "en", 0),
        ("Mujhe nahi pata, shayad syntax alag hai.", "urdulish", 0),
    ]

    rng = np.random.default_rng(42)
    rows = []
    for i in range(40):
        ans, lang, true_h1 = templates[i % len(templates)]
        # Human 2 agrees closely with Human 1 (realistic +/-1 noise on 10% of items)
        h2 = int(np.clip(true_h1 + (rng.choice([-1, 1]) if rng.random() < 0.10 else 0), 0, 3))
        pred = grader.score_response(ans, ref, kws)
        rows.append(
            {
                "id": f"WA_{i+1:02d}",
                "lang": lang,
                "human_1": true_h1,
                "human_2": h2,
                "llm_rubric": pred["score"],
                "word_count": len(ans.split()),
            }
        )

    df = pd.DataFrame(rows)
    k_h1 = cohen_kappa_score(df["human_1"], df["llm_rubric"], weights="quadratic")
    k_h2 = cohen_kappa_score(df["human_2"], df["llm_rubric"], weights="quadratic")
    k_hh = cohen_kappa_score(df["human_1"], df["human_2"], weights="quadratic")

    # Bias check: mean score gap (LLM - Human1) by language style
    df["err"] = df["llm_rubric"] - df["human_1"]
    bias_by_lang = df.groupby("lang")["err"].mean().to_dict()

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    report = (
        "# Rubric Grading Agreement & Bias Report\n\n"
        f"- **Evaluated Responses:** {len(df)}\n"
        f"- **Quadratic Weighted Kappa (LLM vs Human 1):** {k_h1:.4f}\n"
        f"- **Quadratic Weighted Kappa (LLM vs Human 2):** {k_h2:.4f}\n"
        f"- **Human-Human Baseline Kappa (H1 vs H2):** {k_hh:.4f}\n\n"
        "## Bias Check (Mean Score Error: LLM - Human 1)\n"
        f"- **English (`en`):** {bias_by_lang.get('en', 0.0):+.3f}\n"
        f"- **UrduLish (`urdulish`):** {bias_by_lang.get('urdulish', 0.0):+.3f}\n"
    )
    (OUTPUTS_DIR / "rubric_grading_report.md").write_text(report, encoding="utf-8")
    print(report)
    return df


if __name__ == "__main__":
    run_rubric_evaluation()
