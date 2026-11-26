"""Dropout Early-Warning Model (Day 2, Task 5):
- Uses Weeks 1-2 behavioral & performance features to predict pre-Week-4 dropout
- LightGBM classifier with student-level train/test split
- Evaluates PR-AUC and ROC-AUC
- Computes SHAP explanations + saves summary plot
- Maps risk tiers (Low / Medium / High) to concrete tutor/mentor actions
"""

from pathlib import Path
import lightgbm as lgb
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUTS_DIR = BASE_DIR / "outputs"


def build_early_features(profiles: pd.DataFrame, interactions: pd.DataFrame) -> pd.DataFrame:
    """Extract Weeks 1-2 early-warning features per student."""
    early = interactions[interactions["week"] <= 2].copy()
    early["fast_wrong"] = ((early["correct"] == 0) & (early["response_time_sec"] < 15.0)).astype(int)

    agg = (
        early.groupby("student_id", as_index=False)
        .agg(
            early_attempts=("correct", "count"),
            early_accuracy=("correct", "mean"),
            avg_rt_sec=("response_time_sec", "mean"),
            std_rt_sec=("response_time_sec", "std"),
            fast_wrong_rate=("fast_wrong", "mean"),
            concepts_covered=("concept_id", "nunique"),
            max_attempt_on_concept=("attempt_num", "max"),
        )
        .fillna(0.0)
    )
    df = profiles[["student_id", "dropped_out", "dropout_week"]].merge(agg, on="student_id", how="left").fillna(0.0)
    df["target_pre_w4_dropout"] = ((df["dropped_out"] == 1) & (df["dropout_week"] < 4)).astype(int)
    return df


def assign_risk_action(prob: float) -> tuple[str, str]:
    if prob >= 0.60:
        return "High", "Trigger 1-on-1 mentor check-in, switch to scaffolded ZPD review, send UrduLish encouragement."
    elif prob >= 0.35:
        return "Medium", "Insert spaced-repetition refresher + Socratic hint prompts on prerequisite gaps."
    return "Low", "Continue adaptive ZPD path with standard spaced repetition."


def run_dropout_model():
    profiles = pd.read_csv(DATA_DIR / "student_profiles.csv")
    interactions = pd.read_csv(DATA_DIR / "learner_interactions.csv")
    df = build_early_features(profiles, interactions)

    feature_cols = [
        "early_attempts",
        "early_accuracy",
        "avg_rt_sec",
        "std_rt_sec",
        "fast_wrong_rate",
        "concepts_covered",
        "max_attempt_on_concept",
    ]
    X = df[feature_cols]
    y = df["target_pre_w4_dropout"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    model = lgb.LGBMClassifier(
        n_estimators=150,
        learning_rate=0.05,
        max_depth=4,
        num_leaves=15,
        random_state=42,
        verbose=-1,
    )
    model.fit(X_train, y_train)

    y_prob = model.predict_proba(X_test)[:, 1]
    pr_auc = average_precision_score(y_test, y_prob)
    roc_auc = roc_auc_score(y_test, y_prob)

    # SHAP explanations
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)
    if isinstance(shap_values, list):
        shap_vals = shap_values[1]
    else:
        shap_vals = shap_values

    plt.figure(figsize=(8, 4.5))
    shap.summary_plot(shap_vals, X_test, show=False)
    plt.title("LightGBM Dropout Early-Warning — SHAP Feature Impact", fontweight="bold")
    plt.tight_layout()
    plt.savefig(OUTPUTS_DIR / "dropout_shap_summary.png", dpi=150, bbox_inches="tight")
    plt.close()

    # Risk tier breakdown on test set
    risk_rows = []
    for p in y_prob:
        tier, action = assign_risk_action(float(p))
        risk_rows.append({"prob": round(float(p), 4), "risk_tier": tier, "action": action})
    risk_df = pd.DataFrame(risk_rows)
    tier_counts = risk_df["risk_tier"].value_counts().to_dict()

    mean_abs_shap = pd.Series(np.abs(shap_vals).mean(axis=0), index=feature_cols).sort_values(ascending=False)

    report = (
        "# Dropout Early-Warning Model Report (LightGBM + SHAP)\n\n"
        f"- **Test Students:** {len(X_test)} (Pre-Week-4 dropout prevalence: {y_test.mean():.1%})\n"
        f"- **PR-AUC:** {pr_auc:.4f}\n"
        f"- **ROC-AUC:** {roc_auc:.4f}\n\n"
        "## Top SHAP Drivers\n"
        + "\n".join(f"- `{feat}`: mean |SHAP| = {val:.4f}" for feat, val in mean_abs_shap.items())
        + "\n\n## Risk Tiers & Intervention Actions\n"
        f"- **High (>= 0.60)** ({tier_counts.get('High', 0)} students): {assign_risk_action(0.75)[1]}\n"
        f"- **Medium (0.35 - 0.59)** ({tier_counts.get('Medium', 0)} students): {assign_risk_action(0.45)[1]}\n"
        f"- **Low (< 0.35)** ({tier_counts.get('Low', 0)} students): {assign_risk_action(0.15)[1]}\n"
    )
    (OUTPUTS_DIR / "dropout_report.md").write_text(report, encoding="utf-8")
    print(f"LightGBM Dropout Model -> PR-AUC: {pr_auc:.4f} | ROC-AUC: {roc_auc:.4f}")
    print("Risk tier counts:", tier_counts)
    return pr_auc, roc_auc


if __name__ == "__main__":
    run_dropout_model()
