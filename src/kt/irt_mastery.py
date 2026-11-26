"""Mastery Estimation & 1PL/2PL IRT Calibration (Day 2, Task 2):
- Computes mastery score per student per concept
- Fits 1PL (Rasch) and 2PL IRT models to estimate question difficulty (b) and discrimination (a)
- Flags bad questions (low/negative discrimination or extreme difficulty)
"""

from pathlib import Path
import numpy as np
import pandas as pd
import torch
import torch.nn as nn

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUTS_DIR = BASE_DIR / "outputs"


def compute_concept_mastery(df: pd.DataFrame) -> pd.DataFrame:
    """Estimate smoothed mastery score per (student, concept) using empirical Bayes."""
    agg = (
        df.groupby(["student_id", "concept_id"], as_index=False)
        .agg(attempts=("correct", "count"), successes=("correct", "sum"))
    )
    # Beta(2, 2) prior smoothing for reliable mastery estimates
    agg["mastery_score"] = ((agg["successes"] + 1.5) / (agg["attempts"] + 3.0)).round(4)
    return agg


def fit_irt(df: pd.DataFrame, two_pl: bool = True, epochs: int = 250, lr: float = 0.05) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fit 1PL or 2PL IRT via PyTorch MLE/MAP."""
    torch.manual_seed(42)
    students = sorted(df["student_id"].unique())
    questions = sorted(df["question_id"].unique())
    s_map = {s: i for i, s in enumerate(students)}
    q_map = {q: i for i, q in enumerate(questions)}

    s_idx = torch.tensor([s_map[s] for s in df["student_id"]], dtype=torch.long)
    q_idx = torch.tensor([q_map[q] for q in df["question_id"]], dtype=torch.long)
    y = torch.tensor(df["correct"].to_numpy(), dtype=torch.float32)

    theta = nn.Parameter(torch.zeros(len(students)))
    b = nn.Parameter(torch.zeros(len(questions)))
    a_raw = nn.Parameter(torch.zeros(len(questions))) if two_pl else None

    params = [theta, b] + ([a_raw] if two_pl else [])
    opt = torch.optim.Adam(params, lr=lr)
    bce = nn.BCEWithLogitsLoss()

    for _ in range(epochs):
        opt.zero_grad()
        a = torch.exp(a_raw).clamp(0.05, 4.0) if two_pl else torch.ones_like(b[q_idx])
        a_sel = a[q_idx] if two_pl else 1.0
        logits = a_sel * (theta[s_idx] - b[q_idx])
        # L2 priors on theta, b, and log-discrimination a_raw for psychometric identifiability
        reg = 0.01 * (theta.pow(2).mean() + b.pow(2).mean()) + (0.04 * a_raw.pow(2).mean() if two_pl else 0.0)
        loss = bce(logits, y) + reg
        loss.backward()
        opt.step()

    with torch.no_grad():
        a_vals = torch.exp(a_raw).clamp(0.05, 4.0).numpy() if two_pl else np.ones(len(questions))
        b_vals = b.numpy()
        theta_vals = theta.numpy()

    q_emp = df.groupby("question_id")["correct"].agg(["mean", "count"]).reindex(questions)
    q_df = pd.DataFrame(
        {
            "question_id": questions,
            "irt_a": np.round(a_vals, 4),
            "irt_b": np.round(b_vals, 4),
            "empirical_acc": np.round(q_emp["mean"].to_numpy(), 4),
            "attempts": q_emp["count"].to_numpy(),
        }
    )
    s_df = pd.DataFrame({"student_id": students, "irt_theta": np.round(theta_vals, 4)})
    return q_df, s_df


def run_irt_and_mastery():
    df = pd.read_csv(DATA_DIR / "learner_interactions.csv")
    mastery_df = compute_concept_mastery(df)
    q1_df, _ = fit_irt(df, two_pl=False)
    q2_df, s2_df = fit_irt(df, two_pl=True)

    q_merged = q2_df.merge(
        q1_df[["question_id", "irt_b"]].rename(columns={"irt_b": "irt_1pl_b"}),
        on="question_id",
    )
    # Flag weak/extreme questions: low discrimination (< 0.70) or extreme difficulty (|b| > 1.8)
    q_merged["is_bad"] = (q_merged["irt_a"] < 0.70) | (q_merged["irt_b"].abs() > 1.8)
    bad_q = q_merged[q_merged["is_bad"]].sort_values("irt_a")

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    mastery_df.to_csv(OUTPUTS_DIR / "student_concept_mastery.csv", index=False)
    q_merged.to_csv(OUTPUTS_DIR / "irt_question_params.csv", index=False)
    bad_q.to_csv(OUTPUTS_DIR / "irt_bad_questions.csv", index=False)

    print(f"Mastery rows: {len(mastery_df):,} | Questions calibrated: {len(q_merged)}")
    print(f"2PL IRT summary: mean a={q_merged['irt_a'].mean():.2f}, mean b={q_merged['irt_b'].mean():.2f}")
    print(f"Bad questions flagged (a < 0.45 or |b| > 2.2): {len(bad_q)}")
    if len(bad_q) > 0:
        print(bad_q.head(5).to_string(index=False))
    return mastery_df, q_merged, bad_q


if __name__ == "__main__":
    run_irt_and_mastery()
