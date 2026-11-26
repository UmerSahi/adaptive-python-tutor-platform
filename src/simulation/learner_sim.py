"""Learner Data Loader (ASSISTments / EdNet) & 1,000-Student Simulator for Ilm Academy.

Models each student with:
- ability (theta)
- speed (response-time multiplier)
- slip (P(wrong | mastered))
- guess (P(correct | not mastered))
- dropout (pre-Week-4 ~45% attrition calibrated to Ilm Academy)
"""

import json
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np
import pandas as pd

from src.graph.concept_graph import build_concept_graph

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"


def generate_assistments_sample(
    out_path: Path = RAW_DIR / "assistments_sample.csv",
    n_rows: int = 2000,
    seed: int = 42,
) -> Path:
    """Create a realistic ASSISTments-schema CSV so the loader is testable out-of-the-box."""
    rng = np.random.default_rng(seed)
    skills = ["variables", "if_elif_else", "for_loops", "lists", "dictionaries", "recursion"]
    df = pd.DataFrame(
        {
            "user_id": rng.integers(10001, 10201, size=n_rows),
            "problem_id": rng.integers(1, 120, size=n_rows),
            "skill_name": rng.choice(skills, size=n_rows),
            "correct": rng.binomial(1, 0.68, size=n_rows),
            "ms_first_response": rng.lognormal(mean=9.4, sigma=0.6, size=n_rows).astype(int),
            "attempt_count": rng.integers(1, 5, size=n_rows),
        }
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    return out_path


def load_external_learner_data(
    path: Path, dataset_type: str = "assistments"
) -> pd.DataFrame:
    """Load and normalize ASSISTments or EdNet interaction logs to a unified schema."""
    df = pd.read_csv(path)
    if dataset_type.lower() == "assistments":
        norm = pd.DataFrame(
            {
                "student_id": "AS_" + df["user_id"].astype(str),
                "question_id": "AS_Q" + df["problem_id"].astype(str),
                "concept_id": df["skill_name"].fillna("unknown").astype(str),
                "correct": df["correct"].astype(int),
                "response_time_sec": (df["ms_first_response"].clip(lower=500) / 1000.0).round(2),
                "attempt_num": df.get("attempt_count", pd.Series(1, index=df.index)).astype(int),
                "source": "assistments",
            }
        )
        return norm
    elif dataset_type.lower() == "ednet":
        norm = pd.DataFrame(
            {
                "student_id": "ED_" + df["user_id"].astype(str),
                "question_id": df["question_id"].astype(str),
                "concept_id": df.get("tags", pd.Series("unknown", index=df.index)).astype(str),
                "correct": (df["user_answer"] == df["correct_answer"]).astype(int),
                "response_time_sec": (df["elapsed_time"].clip(lower=500) / 1000.0).round(2),
                "attempt_num": 1,
                "source": "ednet",
            }
        )
        return norm
    else:
        raise ValueError(f"Unsupported dataset_type: {dataset_type}")


def _sigmoid(x: float) -> float:
    return float(1.0 / (1.0 + np.exp(-np.clip(x, -15.0, 15.0))))


def simulate_learners(
    n_students: int = 1000,
    seed: int = 42,
    question_bank_path: Path = DATA_DIR / "question_bank.json",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Simulate 1,000 students progressing through Ilm Academy's 45-concept Python path."""
    rng = np.random.default_rng(seed)
    G = build_concept_graph(question_bank_path)
    topo_concepts = list(nx.topological_sort(G))
    questions = json.loads(question_bank_path.read_text(encoding="utf-8"))

    q_by_concept: dict[str, list[dict[str, Any]]] = {}
    for q in questions:
        q_by_concept.setdefault(q["concept_id"], []).append(q)

    # Hard/bottleneck concepts that naturally induce higher cognitive load
    bottleneck_penalty = {
        "nested_conditionals": 0.35,
        "while_loops": 0.45,
        "nested_loops": 0.65,
        "mutability": 0.60,
        "nested_structures": 0.55,
        "hashing_concepts": 0.65,
        "variable_scope": 0.60,
        "recursion": 0.90,
        "generators": 0.70,
        "time_complexity": 0.85,
    }

    profiles = []
    interactions = []

    for idx in range(1, n_students + 1):
        sid = f"S{idx:04d}"
        ability = float(rng.normal(0.0, 1.0))
        speed = float(np.clip(rng.lognormal(mean=0.0, sigma=0.35), 0.4, 2.5))
        slip = float(np.clip(rng.beta(2.0, 18.0), 0.02, 0.25))
        guess = float(np.clip(rng.beta(2.0, 14.0), 0.05, 0.30))
        dropout_propensity = float(rng.beta(2.2, 3.0))  # drives ~45% pre-week-4 attrition

        concept_mastery: dict[str, float] = {}
        dropped_out = False
        dropout_week = None
        dropout_concept = None
        consecutive_wrong = 0

        for cid in topo_concepts:
            node = G.nodes[cid]
            week = int(node["week"])
            prereqs = list(G.predecessors(cid))

            # Prerequisite gap penalty if student struggled on prerequisites
            prereq_gap = 0.0
            if prereqs:
                avg_pre = np.mean([concept_mastery.get(p, 0.5) for p in prereqs])
                if avg_pre < 0.55:
                    prereq_gap = 0.75 * (0.55 - avg_pre) * 2.0

            c_questions = q_by_concept.get(cid, [])
            # Each student attempts 1 to 3 questions on this concept (adaptive practice)
            local_theta = ability - prereq_gap - bottleneck_penalty.get(cid, 0.0)
            c_correct_count = 0
            c_attempts = 0

            for attempt_idx, q in enumerate(rng.permutation(c_questions)[:3], start=1):
                c_attempts += 1
                # Learning gain across attempts on the same concept
                effective_theta = local_theta + 0.28 * (attempt_idx - 1)
                p_master = _sigmoid(1.35 * (effective_theta - float(q["irt_b"])))
                p_correct = guess + (1.0 - slip - guess) * p_master
                correct = int(rng.random() < p_correct)
                c_correct_count += correct

                # Response time scales with question difficulty and inverse speed
                base_time = 18.0 + 14.0 * max(0.0, float(q["irt_b"]) + 1.5)
                if q["type"] == "coding":
                    base_time *= 2.4
                elif q["type"] == "short_answer":
                    base_time *= 1.4
                rt = float(np.clip(rng.lognormal(np.log(base_time / speed), 0.35), 4.0, 420.0))

                interactions.append(
                    {
                        "student_id": sid,
                        "concept_id": cid,
                        "week": week,
                        "lesson_id": node["lesson_id"],
                        "question_id": q["id"],
                        "question_type": q["type"],
                        "difficulty": q["difficulty"],
                        "bloom_level": q["bloom_level"],
                        "attempt_num": attempt_idx,
                        "correct": correct,
                        "response_time_sec": round(rt, 2),
                        "p_correct_true": round(p_correct, 4),
                    }
                )

                if correct == 0:
                    consecutive_wrong += 1
                else:
                    consecutive_wrong = 0

                # Early stop on concept if already mastered
                if attempt_idx >= 2 and c_correct_count >= 2:
                    break

            concept_mastery[cid] = c_correct_count / max(1, c_attempts)

            # Dropout hazard: calibrated to ~45% pre-Week-4 attrition across 27 early concepts
            if week <= 3:
                hazard = (
                    0.004
                    + 0.022 * dropout_propensity
                    + (0.035 if consecutive_wrong >= 3 else 0.0)
                    + (0.015 if ability < -0.5 else 0.0)
                )
            else:
                hazard = 0.004 + 0.010 * dropout_propensity + (0.020 if consecutive_wrong >= 4 else 0.0)

            if rng.random() < hazard:
                dropped_out = True
                dropout_week = week
                dropout_concept = cid
                break

        profiles.append(
            {
                "student_id": sid,
                "ability": round(ability, 4),
                "speed": round(speed, 4),
                "slip": round(slip, 4),
                "guess": round(guess, 4),
                "dropout_propensity": round(dropout_propensity, 4),
                "dropped_out": int(dropped_out),
                "dropout_week": dropout_week if dropped_out else 0,
                "dropout_concept": dropout_concept if dropped_out else "completed",
            }
        )

    profiles_df = pd.DataFrame(profiles)
    interactions_df = pd.DataFrame(interactions)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    profiles_df.to_csv(DATA_DIR / "student_profiles.csv", index=False)
    interactions_df.to_csv(DATA_DIR / "learner_interactions.csv", index=False)
    return profiles_df, interactions_df


if __name__ == "__main__":
    sample_path = generate_assistments_sample()
    ext_df = load_external_learner_data(sample_path, "assistments")
    print(f"Loaded ASSISTments sample: {len(ext_df)} rows, {ext_df['student_id'].nunique()} students.")

    prof_df, inter_df = simulate_learners(n_students=1000, seed=42)
    pre_w4_drop = ((prof_df["dropped_out"] == 1) & (prof_df["dropout_week"] < 4)).mean()
    total_drop = prof_df["dropped_out"].mean()
    print(f"Simulated {len(prof_df)} students, {len(inter_df)} interactions.")
    print(f"Pre-Week-4 dropout rate: {pre_w4_drop:.1%} | Overall dropout rate: {total_drop:.1%}")
    print(f"Overall accuracy: {inter_df['correct'].mean():.1%}")
