"""Ilm Academy Teacher & Student Streamlit App (Day 5, Tasks 1 & 3):
- Role-based view switcher: Teacher Dashboard vs. Student Learning App
- Teacher Dashboard: class mastery heatmap, weak concepts, at-risk students, grading queue + side-by-side plagiarism flags, question bank health, tutor usage
- Student App: personalized learning path (Ali/Sara), Socratic AI Tutor (English/UrduLish, Hint Ladder), and live sandboxed code submission
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

from src.grading.code_grader import grade_submission
from src.tutor.socratic_tutor import SocraticTutor

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUTS_DIR = BASE_DIR / "outputs"

st.set_page_config(page_title="Ilm Academy AI Tutor & Analytics", layout="wide")
st.title("Ilm Academy — AI Tutor & Adaptive Learning Platform")

role = st.sidebar.selectbox("Role (RBAC View)", ["Teacher", "Student"])

if role == "Teacher":
    st.header("Teacher Dashboard")
    profiles = pd.read_csv(DATA_DIR / "student_profiles.csv")
    interactions = pd.read_csv(DATA_DIR / "learner_interactions.csv")
    mastery = pd.read_csv(OUTPUTS_DIR / "student_concept_mastery.csv")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Active Cohort", f"{len(profiles):,} students")
    c2.metric("Mean Accuracy", f"{interactions['correct'].mean():.1%}")
    pre_w4 = ((profiles["dropped_out"] == 1) & (profiles["dropout_week"] < 4)).mean()
    c3.metric("Pre-Week-4 Dropout", f"{pre_w4:.1%}")
    c4.metric("Question Bank", "225 items (IRT OK)")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Mastery Heatmap & Weak Concepts",
        "At-Risk Students",
        "Grading & Plagiarism Queue",
        "Question Bank Health",
        "Tutor Usage & Safety",
    ])

    with tab1:
        st.subheader("Class Mastery Heatmap (Top 20 Students x Top 12 Concepts)")
        sample_m = mastery.pivot(index="student_id", columns="concept_id", values="mastery_score").iloc[:20, :12]
        fig, ax = plt.subplots(figsize=(12, 5))
        sns.heatmap(sample_m, cmap="RdYlGn", vmin=0, vmax=1, ax=ax)
        st.pyplot(fig)

        st.subheader("Weakest Concepts")
        weak = interactions.groupby("concept_id", as_index=False)["correct"].mean().sort_values("correct").head(10)
        st.dataframe(weak, use_container_width=True)

    with tab2:
        st.subheader("At-Risk Students (Pre-Week-4 Dropout Early Warning)")
        at_risk = profiles[profiles["dropped_out"] == 1][["student_id", "ability", "dropout_week", "dropout_concept"]].head(25)
        st.dataframe(at_risk, use_container_width=True)

    with tab3:
        st.subheader("Auto-Grading Queue & Plagiarism Flags (Flag-Only Policy)")
        if (OUTPUTS_DIR / "grading_teacher_comparison.csv").exists():
            st.dataframe(pd.read_csv(OUTPUTS_DIR / "grading_teacher_comparison.csv").head(15), use_container_width=True)
        if (OUTPUTS_DIR / "plagiarism_flagged_pairs.json").exists():
            flags = json.loads((OUTPUTS_DIR / "plagiarism_flagged_pairs.json").read_text(encoding="utf-8"))
            for fl in flags:
                with st.expander(f"Flagged Pair {fl['pair_id']} — Score: {fl['combined_score']} (Human Review Required)"):
                    col_a, col_b = st.columns(2)
                    col_a.code(fl["code_a"], language="python")
                    col_b.code(fl["code_b"], language="python")

    with tab4:
        st.subheader("Question Bank Health (2PL IRT)")
        if (OUTPUTS_DIR / "irt_question_params.csv").exists():
            st.dataframe(pd.read_csv(OUTPUTS_DIR / "irt_question_params.csv").head(20), use_container_width=True)

    with tab5:
        st.subheader("Socratic Tutor Safety & Evaluation")
        if (OUTPUTS_DIR / "tutor_evaluation_summary.md").exists():
            st.markdown((OUTPUTS_DIR / "tutor_evaluation_summary.md").read_text(encoding="utf-8"))

else:
    st.header("Student Learning Workspace")
    if (OUTPUTS_DIR / "adaptive_learning_paths.json").exists():
        paths = json.loads((OUTPUTS_DIR / "adaptive_learning_paths.json").read_text(encoding="utf-8"))
        student_name = st.selectbox("Select Persona", list(paths.keys()))
        st.info(paths[student_name]["urdulish_message"])
        st.dataframe(pd.DataFrame(paths[student_name]["path"]), use_container_width=True)

    st.subheader("Socratic AI Tutor (Grounded RAG + Hint Ladder)")
    col1, col2, col3 = st.columns(3)
    lang = col1.selectbox("Language", ["en", "urdulish"])
    stage = col2.slider("Hint Ladder Stage", 1, 4, 1)
    mastery_val = col3.slider("Concept Mastery", 0.0, 1.0, 0.35)
    q_text = st.text_input("Ask a Python question:", "I am stuck on recursion base case at 1am")
    if st.button("Ask Socratic Tutor"):
        tutor = SocraticTutor()
        res = tutor.respond(q_text, mastery_score=mastery_val, hint_stage=stage, language=lang)
        st.success(res["response"])

    st.subheader("Live Code Submission (Sandboxed Auto-Grader)")
    code_input = st.text_area(
        "Write `factorial(n)`:",
        "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)",
        height=130,
    )
    if st.button("Submit Code to Sandbox"):
        res = grade_submission(
            code_input,
            visible_tests=["assert factorial(0) == 1", "assert factorial(3) == 6"],
            hidden_tests=["assert factorial(5) == 120"],
        )
        st.json(res)
