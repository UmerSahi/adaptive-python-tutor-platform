"""Generate the Capstone Presentation Slide Deck (docs/Ilm_Academy_Capstone_Deck.pptx)."""

from pathlib import Path
from pptx import Presentation
from pptx.util import Pt

BASE_DIR = Path(__file__).resolve().parent.parent
OUT_PATH = BASE_DIR / "docs" / "Ilm_Academy_Capstone_Deck.pptx"

SLIDES = [
    ("Ilm Academy: AI Tutor & Adaptive Learning Platform",
     "Week 13 Capstone Handover | Solving 45% Pre-Week-4 Dropout Across 8,000 Students"),
    ("Day 1: Content Pipeline, 45-Concept DAG & Question Bank",
     "- Whisper video transcription with timestamps + PPTX/PDF extraction -> 87 chunks in ChromaDB\n"
     "- 45-concept Python DAG (74 edges, cycle-free) mapped to 8 lessons & 225 questions\n"
     "- 1,000-student simulator (81,974 interactions, 40.4% pre-Week-4 dropout) + EDA"),
    ("Day 2: Knowledge Tracing, IRT & Adaptive Engine",
     "- Student-split KT: DKT LSTM AUC 0.7376 > BKT 0.6595 > PFA 0.6587 > Baseline 0.6369\n"
     "- Adaptive Engine (ZPD 60-80% + Thompson Sampling + Spaced Repetition): +44% mastery gain, 0% prereq violations\n"
     "- LightGBM Dropout Early-Warning: PR-AUC 0.9183, ROC-AUC 0.9102 with SHAP"),
    ("Day 3: Grounded Socratic Tutor & Question Calibration",
     "- RAG with Lesson + Video Timestamp citations in English & UrduLish + 4-stage Hint Ladder\n"
     "- 50-conversation eval: 0.0% answer leakage, 100% grounding, 100% jailbreak resistance\n"
     "- Question Generator: 93.3% acceptance rate; IRT difficulty calibration r = 0.9313"),
    ("Day 4: Secure Sandbox, Auto-Grader & Plagiarism Detection",
     "- Sandbox: 6/6 attacks defended (infinite loop, fork bomb, env access, network, file I/O, __import__)\n"
     "- Code Grader (50 submissions vs teacher): r = 0.8639, 80% within 10 pts\n"
     "- Rubric Grader: kappa = 0.73 (flagged UrduLish bias); Plagiarism: 100% P/R (Flag-Only)"),
    ("Day 5: Impact Evaluation, A/B Test & Production Handover",
     "- Teacher Hours Saved: ~200 hrs/week on 3,000 Sunday assignments\n"
     "- FastAPI RBAC + Streamlit Teacher/Student App + Docker Compose; 500-req load test passed (0% errors)\n"
     "- 6-week RCT A/B Test: 163 students/arm for 80% power (45% -> 30% dropout)"),
]


def main():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    prs = Presentation()
    for idx, (title, body) in enumerate(SLIDES):
        layout = prs.slide_layouts[0] if idx == 0 else prs.slide_layouts[1]
        slide = prs.slides.add_slide(layout)
        slide.shapes.title.text = title
        tf = slide.placeholders[1].text_frame
        tf.text = body
        for p in tf.paragraphs:
            p.font.size = Pt(18)
    prs.save(OUT_PATH)
    print(f"Saved slide deck -> {OUT_PATH}")


if __name__ == "__main__":
    main()
