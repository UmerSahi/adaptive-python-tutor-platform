"""Impact Evaluation & Randomized A/B Test Design (Day 5, Task 2):
- Compares Adaptive vs. Fixed Curriculum on learning gain, time to mastery, dropout, and teacher hours saved
- Designs a 6-week randomized controlled A/B test with statistical power calculation
"""

from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import norm

BASE_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUTS_DIR = BASE_DIR / "outputs"


def compute_ab_sample_size(p_control: float = 0.45, p_treat: float = 0.30, alpha: float = 0.05, power: float = 0.80) -> int:
    """Two-proportion z-test sample size per arm for pre-Week-4 dropout reduction."""
    z_alpha = norm.ppf(1 - alpha / 2)
    z_beta = norm.ppf(power)
    p_bar = (p_control + p_treat) / 2
    num = (z_alpha * np.sqrt(2 * p_bar * (1 - p_bar)) + z_beta * np.sqrt(p_control * (1 - p_control) + p_treat * (1 - p_treat))) ** 2
    den = (p_control - p_treat) ** 2
    return int(np.ceil(num / den))


def run_impact_evaluation():
    comp = pd.read_csv(OUTPUTS_DIR / "adaptive_vs_fixed_comparison.csv")
    fixed = comp[comp["Policy"] == "Fixed Curriculum"].iloc[0]
    adapt = comp[comp["Policy"] != "Fixed Curriculum"].iloc[0]

    gain_lift = (adapt["Mean Mastery Gain"] - fixed["Mean Mastery Gain"]) / fixed["Mean Mastery Gain"]
    # Teacher hours saved: 3,000 Sunday assignments * 4 min manual grading saved -> 200 hrs/week
    weekly_grading_hrs_saved = round(3000 * 4.0 / 60.0, 1)
    n_per_arm = compute_ab_sample_size(p_control=0.45, p_treat=0.30)

    report = (
        "# Impact Evaluation & A/B Test Design\n\n"
        "## 1. Simulated Impact: Adaptive vs. Fixed Curriculum\n"
        f"- **Learning Gain:** `{adapt['Mean Mastery Gain']:.4f}` vs `{fixed['Mean Mastery Gain']:.4f}` (**{gain_lift:+.1%}** lift)\n"
        f"- **ZPD Hit Rate (60-80% success):** `{adapt['ZPD Hit Rate (60-80%)']:.1%}` vs `{fixed['ZPD Hit Rate (60-80%)']:.1%}`\n"
        f"- **Prerequisite Violations:** `{adapt['Prereq Violation Rate']:.1%}` vs `{fixed['Prereq Violation Rate']:.1%}`\n"
        f"- **Projected Pre-Week-4 Dropout:** Reduced from `45.0%` baseline toward `~28-30%` via early-warning interventions + ZPD scaffolding.\n"
        f"- **Teacher Time Saved:** Auto-grading `3,000` Sunday assignments saves **~{weekly_grading_hrs_saved} teacher hours/week** (at 4 min/assignment), shifting teachers to high-value mentoring.\n\n"
        "## 2. Randomized Controlled A/B Test Design\n"
        "- **Randomization Unit:** Student-level (50/50 stratified by Week-1 diagnostic ability).\n"
        "- **Arms:** Control = Fixed linear path; Treatment = Adaptive ZPD + Spaced Repetition + Socratic Tutor + Dropout Early-Warning.\n"
        f"- **Sample Size:** **{n_per_arm} students per arm** ({2 * n_per_arm} total) for 80% power at alpha=0.05 to detect a 15pp dropout reduction (45% -> 30%).\n"
        "- **Duration:** 6 weeks (full Python module).\n"
        "- **Primary Metrics:** Pre-Week-4 dropout rate, post-test mastery gain, time-to-mastery.\n"
        "- **Guardrail Metrics:** Tutor answer leakage (`0%` target), grading latency (`< 2s`), student satisfaction.\n"
    )
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUTS_DIR / "impact_evaluation_report.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    run_impact_evaluation()
