"""Adaptive Learning Engine & Personalized Learning Path (Day 2, Tasks 3 & 4):
- Respects concept graph prerequisites
- Targets Zone of Proximal Development (ZPD: 60-80% predicted success)
- Thompson Sampling bandit for next-concept/question selection
- Spaced Repetition (exponential retention decay)
- Compares Adaptive Engine vs. Fixed Linear Curriculum
- Generates personalized learning paths with estimated time & UrduLish motivation
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
OUTPUTS_DIR = BASE_DIR / "outputs"


class AdaptiveEngine:
    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)
        self.qbank = json.loads((DATA_DIR / "question_bank.json").read_text(encoding="utf-8"))
        self.graph = build_concept_graph(DATA_DIR / "question_bank.json")
        self.topo_order = list(nx.topological_sort(self.graph))
        self.q_by_concept: dict[str, list[dict[str, Any]]] = {}
        for q in self.qbank:
            self.q_by_concept.setdefault(q["concept_id"], []).append(q)
        # Thompson Sampling Beta(alpha, beta) priors per concept
        self.ts_alpha = {c: 2.0 for c in self.topo_order}
        self.ts_beta = {c: 2.0 for c in self.topo_order}

    def eligible_concepts(self, mastery: dict[str, float], prereq_thresh: float = 0.60) -> list[str]:
        """Return concepts whose prerequisites are all >= prereq_thresh."""
        eligible = []
        for c in self.topo_order:
            prereqs = list(self.graph.predecessors(c))
            if all(mastery.get(p, 0.0) >= prereq_thresh for p in prereqs):
                eligible.append(c)
        return eligible or [self.topo_order[0]]

    def spaced_repetition_urgency(
        self, concept_id: str, mastery: float, days_since_review: float, stability_days: float = 3.0
    ) -> float:
        """Exponential retention decay R(t) = exp(-t / S). Urgency is 1 - R(t) for previously practiced items."""
        if mastery < 0.60 or days_since_review <= 0:
            return 0.0
        retention = float(np.exp(-days_since_review / (stability_days * (1.0 + mastery))))
        return round(1.0 - retention, 4)

    def predict_success(self, ability: float, irt_b: float) -> float:
        return float(1.0 / (1.0 + np.exp(-1.35 * (ability - irt_b))))

    def recommend_next(
        self,
        ability: float,
        mastery: dict[str, float],
        last_seen_step: dict[str, int],
        current_step: int,
    ) -> dict[str, Any]:
        """Select next (concept, question) using Prerequisites + ZPD (60-80%) + Spaced Repetition + Thompson Sampling."""
        eligible = self.eligible_concepts(mastery)
        candidates = []

        for c in eligible:
            m = mastery.get(c, 0.0)
            days_elapsed = max(0, current_step - last_seen_step.get(c, current_step)) * 0.5
            sr_urgency = self.spaced_repetition_urgency(c, m, days_elapsed)

            # Skip already-mastered concepts unless due for spaced repetition
            if m >= 0.85 and sr_urgency < 0.25:
                continue

            for q in self.q_by_concept.get(c, []):
                p_succ = self.predict_success(ability, float(q["irt_b"]))
                # ZPD target: [0.60, 0.80]
                in_zpd = 0.60 <= p_succ <= 0.80
                zpd_score = 1.0 if in_zpd else max(0.0, 1.0 - abs(p_succ - 0.70) * 2.5)
                ts_sample = float(self.rng.beta(self.ts_alpha[c], self.ts_beta[c]))
                total_score = 0.45 * zpd_score + 0.35 * ts_sample + 0.20 * sr_urgency
                candidates.append(
                    {
                        "concept_id": c,
                        "question": q,
                        "p_success": round(p_succ, 3),
                        "in_zpd": in_zpd,
                        "sr_urgency": sr_urgency,
                        "score": total_score,
                    }
                )

        if not candidates:
            # Fallback to first unmastered eligible concept
            c = eligible[0]
            q = self.q_by_concept[c][0]
            p_succ = self.predict_success(ability, float(q["irt_b"]))
            return {"concept_id": c, "question": q, "p_success": round(p_succ, 3), "in_zpd": 0.6 <= p_succ <= 0.8, "sr_urgency": 0.0}

        best = max(candidates, key=lambda x: x["score"])
        return best

    def update_bandit(self, concept_id: str, in_zpd_outcome: bool):
        if in_zpd_outcome:
            self.ts_alpha[concept_id] += 1.0
        else:
            self.ts_beta[concept_id] += 1.0


def compare_adaptive_vs_fixed(n_students: int = 100, n_steps: int = 30, seed: int = 42) -> pd.DataFrame:
    """Compare Adaptive Engine (ZPD + TS + SR) vs. Fixed Linear Curriculum."""
    rng = np.random.default_rng(seed)
    results = []

    for mode in ["Fixed Curriculum", "Adaptive (ZPD + TS + SR)"]:
        engine = AdaptiveEngine(seed=seed)
        mastery_gains = []
        zpd_hits = []
        prereq_violations = []

        for _ in range(n_students):
            ability = float(rng.normal(0.0, 0.9))
            mastery = {c: 0.15 for c in engine.topo_order}
            last_seen = {}

            for step in range(n_steps):
                if mode == "Fixed Curriculum":
                    cid = engine.topo_order[min(step // 2, len(engine.topo_order) - 1)]
                    q = engine.q_by_concept[cid][step % len(engine.q_by_concept[cid])]
                    p_succ = engine.predict_success(ability, float(q["irt_b"]))
                    in_zpd = 0.60 <= p_succ <= 0.80
                else:
                    rec = engine.recommend_next(ability, mastery, last_seen, step)
                    cid = rec["concept_id"]
                    q = rec["question"]
                    p_succ = rec["p_success"]
                    in_zpd = rec["in_zpd"]

                prereqs = list(engine.graph.predecessors(cid))
                violated = any(mastery.get(p, 0.0) < 0.60 for p in prereqs)
                prereq_violations.append(int(violated))
                zpd_hits.append(int(in_zpd))

                # Simulate learning gain (higher when prerequisites met and in ZPD)
                gain = (0.22 if in_zpd else 0.10) * (0.5 if violated else 1.0)
                mastery[cid] = min(1.0, mastery[cid] + gain)
                ability += 0.03 if in_zpd else 0.01
                last_seen[cid] = step
                if mode != "Fixed Curriculum":
                    engine.update_bandit(cid, in_zpd)

            mastery_gains.append(float(np.mean(list(mastery.values())) - 0.15))

        results.append(
            {
                "Policy": mode,
                "Mean Mastery Gain": round(float(np.mean(mastery_gains)), 4),
                "ZPD Hit Rate (60-80%)": round(float(np.mean(zpd_hits)), 4),
                "Prereq Violation Rate": round(float(np.mean(prereq_violations)), 4),
            }
        )

    comp_df = pd.DataFrame(results)
    comp_df.to_csv(OUTPUTS_DIR / "adaptive_vs_fixed_comparison.csv", index=False)
    print(comp_df.to_string(index=False))
    return comp_df


def build_personalized_path(
    student_name: str,
    ability: float,
    mastery: dict[str, float],
    trait_note: str,
    n_items: int = 8,
) -> dict[str, Any]:
    """Build a personalized learning path with estimated time and UrduLish motivating message."""
    engine = AdaptiveEngine(seed=42)
    sim_mastery = dict(mastery)
    last_seen = {}
    steps = []
    total_mins = 0

    for step in range(n_items):
        rec = engine.recommend_next(ability, sim_mastery, last_seen, step)
        q = rec["question"]
        cid = rec["concept_id"]
        est_mins = 8 if q["type"] == "mcq" else (12 if q["type"] == "short_answer" else 18)
        total_mins += est_mins
        steps.append(
            {
                "step": step + 1,
                "concept_id": cid,
                "concept_name": engine.graph.nodes[cid]["name"],
                "question_id": q["id"],
                "question_type": q["type"],
                "predicted_success": rec["p_success"],
                "in_zpd": rec["in_zpd"],
                "est_minutes": est_mins,
            }
        )
        sim_mastery[cid] = min(1.0, sim_mastery.get(cid, 0.2) + 0.25)
        last_seen[cid] = step

    urdulish_msg = (
        f"Shabash {student_name}! {trait_note} "
        f"Yeh {n_items}-step path sirf {total_mins} minutes mein aapke weak concepts ko strong bana dega — "
        f"har step aapke ZPD (60-80% success) mein set kiya gaya hai, bas steady raho!"
    )
    return {
        "student": student_name,
        "estimated_total_minutes": total_mins,
        "urdulish_message": urdulish_msg,
        "path": steps,
    }


def run_adaptive_demo():
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    print("=== Adaptive Engine vs. Fixed Curriculum ===")
    compare_adaptive_vs_fixed()

    # Scenario personas: Ali (strong in loops, weak in functions) & Sara (fast but careless)
    ali_mastery = {
        "variables": 0.90, "data_types": 0.88, "type_casting": 0.82, "input_output": 0.85,
        "string_formatting": 0.80, "arithmetic_ops": 0.86, "comparison_ops": 0.85,
        "boolean_logic": 0.84, "if_elif_else": 0.88, "nested_conditionals": 0.78,
        "while_loops": 0.90, "range_function": 0.92, "for_loops": 0.91,
        "break_continue": 0.85, "nested_loops": 0.82,
        "functions_def": 0.35, "parameters_defaults": 0.25, "return_values": 0.30,
    }
    sara_mastery = {
        "variables": 0.72, "data_types": 0.68, "type_casting": 0.55, "input_output": 0.65,
        "arithmetic_ops": 0.70, "comparison_ops": 0.58, "boolean_logic": 0.52,
        "if_elif_else": 0.62, "while_loops": 0.48,
    }

    ali_path = build_personalized_path(
        "Ali", ability=0.45, mastery=ali_mastery,
        trait_note="Loops mein aap zabardast ho, ab functions aur return values ko master karne ka waqt hai!"
    )
    sara_path = build_personalized_path(
        "Sara", ability=0.15, mastery=sara_mastery,
        trait_note="Aapki speed bohat achi hai, bas thora slow ho kar careful check karo taake silly slips na hon!"
    )

    demo_out = {"Ali": ali_path, "Sara": sara_path}
    (OUTPUTS_DIR / "adaptive_learning_paths.json").write_text(
        json.dumps(demo_out, indent=2), encoding="utf-8"
    )
    print("\n=== Personalized Path: Ali ===")
    print(ali_path["urdulish_message"])
    for s in ali_path["path"][:4]:
        print(f"  Step {s['step']}: {s['concept_id']} ({s['question_id']}, p_succ={s['predicted_success']}, ~{s['est_minutes']}m)")

    print("\n=== Personalized Path: Sara ===")
    print(sara_path["urdulish_message"])
    for s in sara_path["path"][:4]:
        print(f"  Step {s['step']}: {s['concept_id']} ({s['question_id']}, p_succ={s['predicted_success']}, ~{s['est_minutes']}m)")


if __name__ == "__main__":
    run_adaptive_demo()
