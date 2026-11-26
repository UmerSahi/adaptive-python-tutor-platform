"""Build a polished 16:9 widescreen executive slide presentation
(docs/Ilm_Academy_Capstone_Deck.pptx) with custom dark/light styling,
KPI callout cards, tables, and embedded project charts.
"""

from pathlib import Path
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

BASE_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = BASE_DIR / "outputs"
OUT_PATH = BASE_DIR / "docs" / "Ilm_Academy_Capstone_Deck.pptx"

# Color Palette
NAVY = RGBColor(15, 23, 42)        # #0f172a
SLATE = RGBColor(30, 41, 59)       # #1e293b
BLUE = RGBColor(37, 99, 235)       # #2563eb
EMERALD = RGBColor(16, 185, 129)   # #10b981
AMBER = RGBColor(245, 158, 11)     # #f59e0b
LIGHT_BG = RGBColor(248, 250, 252) # #f8fafc
WHITE = RGBColor(255, 255, 255)
TEXT_DARK = RGBColor(15, 23, 42)
TEXT_MUTED = RGBColor(100, 116, 139)
BORDER = RGBColor(203, 213, 225)


def new_deck() -> Presentation:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    return prs


def set_bg(slide, color: RGBColor):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_header(slide, tag: str, title: str):
    # Top accent bar
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.12))
    bar.fill.solid()
    bar.fill.fore_color.rgb = BLUE
    bar.line.fill.background()

    # Tag pill
    tb_tag = slide.shapes.add_textbox(Inches(0.6), Inches(0.28), Inches(4.5), Inches(0.32))
    p = tb_tag.text_frame.paragraphs[0]
    p.text = tag.upper()
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = BLUE

    # Title
    tb_title = slide.shapes.add_textbox(Inches(0.6), Inches(0.55), Inches(12.1), Inches(0.65))
    p2 = tb_title.text_frame.paragraphs[0]
    p2.text = title
    p2.font.size = Pt(26)
    p2.font.bold = True
    p2.font.color.rgb = TEXT_DARK


def add_footer(slide, page_num: int):
    tb = slide.shapes.add_textbox(Inches(0.6), Inches(7.08), Inches(12.1), Inches(0.3))
    p = tb.text_frame.paragraphs[0]
    p.text = f"Ilm Academy — AI Tutor & Adaptive Learning Platform   |   Week 13 Capstone   |   Slide {page_num}/10"
    p.font.size = Pt(10)
    p.font.color.rgb = TEXT_MUTED


def add_card(slide, left: float, top: float, width: float, height: float, title: str, bullets: list[str], accent: RGBColor = BLUE):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    card.fill.solid()
    card.fill.fore_color.rgb = WHITE
    card.line.color.rgb = BORDER
    card.line.width = Pt(1)

    strip = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left), Inches(top), Inches(0.08), Inches(height))
    strip.fill.solid()
    strip.fill.fore_color.rgb = accent
    strip.line.fill.background()

    tb = slide.shapes.add_textbox(Inches(left + 0.22), Inches(top + 0.14), Inches(width - 0.35), Inches(height - 0.25))
    tf = tb.text_frame
    tf.word_wrap = True
    p0 = tf.paragraphs[0]
    p0.text = title
    p0.font.size = Pt(15)
    p0.font.bold = True
    p0.font.color.rgb = TEXT_DARK
    p0.space_after = Pt(6)

    for b in bullets:
        pb = tf.add_paragraph()
        pb.text = f"• {b}"
        pb.font.size = Pt(12.5)
        pb.font.color.rgb = SLATE
        pb.space_after = Pt(4)


def add_kpi_pill(slide, left: float, top: float, width: float, value: str, label: str, accent: RGBColor = EMERALD):
    box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(1.2))
    box.fill.solid()
    box.fill.fore_color.rgb = SLATE
    box.line.color.rgb = accent
    box.line.width = Pt(1.5)

    tb = slide.shapes.add_textbox(Inches(left + 0.15), Inches(top + 0.15), Inches(width - 0.3), Inches(0.95))
    tf = tb.text_frame
    tf.word_wrap = True
    p1 = tf.paragraphs[0]
    p1.text = value
    p1.font.size = Pt(24)
    p1.font.bold = True
    p1.font.color.rgb = accent
    p1.alignment = PP_ALIGN.CENTER

    p2 = tf.add_paragraph()
    p2.text = label
    p2.font.size = Pt(11.5)
    p2.font.color.rgb = WHITE
    p2.alignment = PP_ALIGN.CENTER


def add_image_if_exists(slide, path: Path, left: float, top: float, width: float, height: float):
    if path.exists():
        slide.shapes.add_picture(str(path), Inches(left), Inches(top), width=Inches(width), height=Inches(height))


def build_presentation():
    prs = new_deck()
    blank = prs.slide_layouts[6]

    # ------------------------------------------------------------------
    # SLIDE 1: Hero Title Slide
    # ------------------------------------------------------------------
    s1 = prs.slides.add_slide(blank)
    set_bg(s1, NAVY)
    accent_bar = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.2), Inches(1.2), Inches(0.08))
    accent_bar.fill.solid()
    accent_bar.fill.fore_color.rgb = EMERALD
    accent_bar.line.fill.background()

    tb = s1.shapes.add_textbox(Inches(0.8), Inches(1.45), Inches(11.7), Inches(1.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Ilm Academy: AI Tutor &\nAdaptive Learning Platform"
    p.font.size = Pt(42)
    p.font.bold = True
    p.font.color.rgb = WHITE

    tb_sub = s1.shapes.add_textbox(Inches(0.8), Inches(3.45), Inches(11.0), Inches(0.9))
    tf_sub = tb_sub.text_frame
    tf_sub.word_wrap = True
    ps = tf_sub.paragraphs[0]
    ps.text = "Week 13 Capstone Handover  |  Solving 45% Pre-Week-4 Dropout Across 8,000 Online Students"
    ps.font.size = Pt(18)
    ps.font.color.rgb = RGBColor(203, 213, 225)

    add_kpi_pill(s1, 0.8, 4.9, 2.7, "+44.1%", "Mastery Gain Lift", EMERALD)
    add_kpi_pill(s1, 3.8, 4.9, 2.7, "0.9183", "Dropout PR-AUC", BLUE)
    add_kpi_pill(s1, 6.8, 4.9, 2.7, "0.0%", "Tutor Answer Leakage", EMERALD)
    add_kpi_pill(s1, 9.8, 4.9, 2.7, "~200 hrs/wk", "Teacher Time Saved", AMBER)

    # ------------------------------------------------------------------
    # SLIDE 2: Problem & Solution Architecture
    # ------------------------------------------------------------------
    s2 = prs.slides.add_slide(blank)
    set_bg(s2, LIGHT_BG)
    add_header(s2, "Executive Summary", "From One-Size-Fits-All to Personalized Mastery")
    add_card(
        s2, 0.6, 1.4, 5.9, 5.3,
        "The Challenge at Ilm Academy",
        [
            "8,000 online Python students follow an identical linear curriculum.",
            "45% of students drop out before Week 4 due to unaddressed prerequisite gaps.",
            "3,000 assignments arrive every Sunday, overwhelming manual grading.",
            "Late-night learners (e.g., 1 AM stuck on recursion) lack safe Socratic guidance.",
        ],
        accent=AMBER,
    )
    add_card(
        s2, 6.8, 1.4, 5.9, 5.3,
        "Our 5-Layer AI Platform",
        [
            "Content RAG + 45-Concept DAG: Whisper-transcribed videos, slides, notes & 225 tagged items.",
            "Knowledge Tracing & IRT: DKT LSTM (0.7366 AUC) + SAKT Transformer + 2PL IRT calibration.",
            "Adaptive Engine: ZPD (60-80%), Thompson Sampling & Spaced Repetition + UrduLish paths.",
            "Socratic Tutor: Grounded RAG with video timestamps, 4-stage Hint Ladder & 0% leakage.",
            "Sandboxed Auto-Grader: 6/6 attacks blocked, bilingual rubric grader & Flag-Only plagiarism.",
        ],
        accent=EMERALD,
    )
    add_footer(s2, 2)

    # ------------------------------------------------------------------
    # SLIDE 3: Day 1 - Content Pipeline & Concept Graph
    # ------------------------------------------------------------------
    s3 = prs.slides.add_slide(blank)
    set_bg(s3, LIGHT_BG)
    add_header(s3, "Day 1: Knowledge Map", "Content Ingestion & 45-Concept Python DAG")
    add_card(
        s3, 0.6, 1.4, 4.6, 5.3,
        "Ingestion & Question Bank",
        [
            "8 lesson videos transcribed with OpenAI Whisper (39 timestamped segments).",
            "40 PowerPoint slides & 8 PDF notes extracted via python-pptx & PyMuPDF.",
            "87 chunks indexed in ChromaDB (all-MiniLM-L6-v2).",
            "45 Python concepts, 74 prerequisite edges — verified cycle-free (DAG = True).",
            "225 questions (90 MCQ, 90 short answer, 45 coding) tagged by Bloom's & IRT b.",
        ],
        accent=BLUE,
    )
    add_image_if_exists(s3, OUT_DIR / "concept_graph.png", 5.45, 1.4, 7.3, 5.2)
    add_footer(s3, 3)

    # ------------------------------------------------------------------
    # SLIDE 4: Day 1 - Learner Simulation & EDA
    # ------------------------------------------------------------------
    s4 = prs.slides.add_slide(blank)
    set_bg(s4, LIGHT_BG)
    add_header(s4, "Day 1: Learner Analytics", "1,000-Student Simulator & Pre-Week-4 Dropout EDA")
    add_image_if_exists(s4, OUT_DIR / "eda_dropout_points.png", 0.6, 1.4, 6.2, 3.0)
    add_image_if_exists(s4, OUT_DIR / "eda_learning_curves.png", 7.0, 1.4, 5.7, 3.0)
    add_card(
        s4, 0.6, 4.6, 12.1, 2.2,
        "Key Empirical Insights (81,974 Interactions | ASSISTments-Compatible Loader)",
        [
            "Dropout Points: 40.4% of simulated students drop out before Week 4, peaking at early bottleneck concepts.",
            "Hardest Concepts: 'time_complexity' (24.1% acc, 91s avg) vs 'if_elif_else' (71.9% acc).",
            "Learning Curves: Accuracy improves +1.8% from attempt 1 (52.7%) to attempt 3 (54.4%) across ability tiers.",
        ],
        accent=EMERALD,
    )
    add_footer(s4, 4)

    # ------------------------------------------------------------------
    # SLIDE 5: Day 2 - Knowledge Tracing Comparison
    # ------------------------------------------------------------------
    s5 = prs.slides.add_slide(blank)
    set_bg(s5, LIGHT_BG)
    add_header(s5, "Day 2: Knowledge Tracing", "5-Model Comparison (Strict Student-Level Split)")
    add_image_if_exists(s5, OUT_DIR / "kt_model_comparison.png", 0.6, 1.45, 6.4, 4.2)
    add_card(
        s5, 7.2, 1.45, 5.5, 5.2,
        "Test Set Performance (Unseen Students)",
        [
            "DKT (PyTorch LSTM): AUC 0.7366 | Acc 67.8% | RMSE 0.4550",
            "SAKT (Transformer): AUC 0.7193 | Acc 66.6% | RMSE 0.4644",
            "BKT (EM/MLE): AUC 0.6595 | Acc 62.2% | RMSE 0.4790",
            "PFA (Logistic): AUC 0.6587 | Acc 62.3% | RMSE 0.4792",
            "Baseline (Concept Mean): AUC 0.6369 | Acc 60.9% | RMSE 0.4837",
            "2PL IRT calibrated all 225 items (r = 0.9313 vs authored b).",
        ],
        accent=BLUE,
    )
    add_footer(s5, 5)

    # ------------------------------------------------------------------
    # SLIDE 6: Day 2 - Adaptive Engine & Learning Paths
    # ------------------------------------------------------------------
    s6 = prs.slides.add_slide(blank)
    set_bg(s6, LIGHT_BG)
    add_header(s6, "Day 2: Adaptive Engine", "ZPD + Thompson Sampling + Spaced Repetition")
    add_card(
        s6, 0.6, 1.4, 5.9, 5.3,
        "Adaptive vs. Fixed Curriculum (100 Students x 30 Steps)",
        [
            "Mean Mastery Gain: 0.0703 vs 0.0488 (+44.1% improvement).",
            "ZPD Hit Rate (60-80% success): 71.0% vs 31.3%.",
            "Prerequisite Violation Rate: 0.0% vs 93.3%.",
            "Spaced repetition schedules review using exponential retention decay.",
        ],
        accent=EMERALD,
    )
    add_card(
        s6, 6.8, 1.4, 5.9, 5.3,
        "Personalized Paths & UrduLish Motivation",
        [
            "Ali (Strong in loops, weak in functions): 8-step, 88-min path targeting 'functions_def' & 'type_casting' at ~69% predicted success.",
            "\"Shabash Ali! Loops mein aap zabardast ho, ab functions ko master karne ka waqt hai!\"",
            "Sara (Fast but careless): 8-step, 106-min path with precision checks.",
            "\"Aapki speed bohat achi hai, bas thora slow ho kar careful check karo!\"",
        ],
        accent=BLUE,
    )
    add_footer(s6, 6)

    # ------------------------------------------------------------------
    # SLIDE 7: Day 2 - Dropout Early-Warning
    # ------------------------------------------------------------------
    s7 = prs.slides.add_slide(blank)
    set_bg(s7, LIGHT_BG)
    add_header(s7, "Day 2: Early Warning", "LightGBM Dropout Prediction & SHAP Explanations")
    add_image_if_exists(s7, OUT_DIR / "dropout_shap_summary.png", 0.6, 1.45, 6.6, 4.4)
    add_card(
        s7, 7.4, 1.45, 5.3, 5.2,
        "Weeks 1-2 Early-Warning Performance",
        [
            "PR-AUC: 0.9183  |  ROC-AUC: 0.9102 (250 test students).",
            "High Risk (>=0.60, 92 students): 1-on-1 mentor check-in + scaffolded ZPD reset + UrduLish encouragement.",
            "Medium Risk (0.35-0.59, 14 students): Spaced-repetition refresher + Socratic hint prompts.",
            "Low Risk (<0.35, 144 students): Continue standard adaptive ZPD path.",
        ],
        accent=AMBER,
    )
    add_footer(s7, 7)

    # ------------------------------------------------------------------
    # SLIDE 8: Day 3 - Grounded Socratic Tutor & Question Gen
    # ------------------------------------------------------------------
    s8 = prs.slides.add_slide(blank)
    set_bg(s8, LIGHT_BG)
    add_header(s8, "Day 3: Socratic AI Tutor", "Grounded RAG, Hint Ladder & Question Calibration")
    add_card(
        s8, 0.6, 1.4, 5.9, 5.3,
        "50-Conversation Tutor Safety Evaluation",
        [
            "Answer Leakage Rate: 0.0% (Target: 0.0%).",
            "Course Grounding (Lesson + Video Timestamp): 100.0%.",
            "Socratic Pedagogy & Positive Tone: 100.0%.",
            "Jailbreak & Prompt-Injection Resistance: 100.0%.",
            "4-Stage Hint Ladder: Guiding Question -> Concept Pointer -> Partial Hint -> Similar Example (English & UrduLish).",
        ],
        accent=EMERALD,
    )
    add_card(
        s8, 6.8, 1.4, 5.9, 5.3,
        "Automated Question Generation & Calibration",
        [
            "Generated 15 new items: MCQs with misconception distractors, short answers & coding tasks with unit tests.",
            "AST + Execution Validator: 14/15 accepted (93.3%); 1 buggy item caught and rejected.",
            "Difficulty Calibration (n=225): Pearson r = 0.9313 (p = 8.99e-100), MAE = 0.4760.",
        ],
        accent=BLUE,
    )
    add_footer(s8, 8)

    # ------------------------------------------------------------------
    # SLIDE 9: Day 4 - Secure Sandbox, Auto-Grader & Plagiarism
    # ------------------------------------------------------------------
    s9 = prs.slides.add_slide(blank)
    set_bg(s9, LIGHT_BG)
    add_header(s9, "Day 4: Grading & Integrity", "Secure Sandbox, Bilingual Rubric & Flag-Only Plagiarism")
    add_card(
        s9, 0.6, 1.4, 5.9, 2.5,
        "Sandbox Security (6/6 Attacks Defended)",
        [
            "Infinite Loop -> Timeout (1.59s) | Fork Bomb, Env Access, Network, File Write, __import__ -> Blocked.",
            "Docker-ready: --network=none --cpus=0.5 --memory=128m --pids-limit=32.",
        ],
        accent=AMBER,
    )
    add_card(
        s9, 0.6, 4.15, 5.9, 2.55,
        "Code Auto-Grader (50 Submissions vs Teacher)",
        [
            "Pearson r = 0.8639 | 80.0% within 10 pts of human teacher marks.",
            "AST McCabe complexity + 1 actionable improvement + lesson link (no solution leak).",
        ],
        accent=BLUE,
    )
    add_card(
        s9, 6.8, 1.4, 5.9, 2.5,
        "Bilingual Rubric Grader (40 Written Answers)",
        [
            "Quadratic Weighted Kappa: 0.9167 (vs H1) & 0.8862 (vs H2).",
            "UrduLish Bias Eliminated: -1.000 -> +0.000 via bilingual synonym normalization.",
        ],
        accent=EMERALD,
    )
    add_card(
        s9, 6.8, 4.15, 5.9, 2.55,
        "MOSS-Style Plagiarism Detector (Flag-Only)",
        [
            "AST 3-gram Jaccard + Embeddings: 100.0% Precision & 100.0% Recall (30 pairs).",
            "Side-by-side teacher diff view; never auto-punishes.",
        ],
        accent=EMERALD,
    )
    add_footer(s9, 9)

    # ------------------------------------------------------------------
    # SLIDE 10: Day 5 - Deployment, Load Test & A/B Test Plan
    # ------------------------------------------------------------------
    s10 = prs.slides.add_slide(blank)
    set_bg(s10, NAVY)
    add_kpi_pill(s10, 0.6, 1.5, 2.8, "105.0 req/s", "500 Reqs in 4.76s (0% Err)", EMERALD)
    add_kpi_pill(s10, 3.7, 1.5, 2.8, "17.4 ms", "Median API Latency (p50)", BLUE)
    add_kpi_pill(s10, 6.8, 1.5, 2.8, "326 Students", "6-Week RCT (80% Power)", AMBER)
    add_kpi_pill(s10, 9.9, 1.5, 2.8, "RBAC 403/200", "Student/Teacher Isolation", EMERALD)

    tb10 = s10.shapes.add_textbox(Inches(0.6), Inches(0.45), Inches(12.1), Inches(0.75))
    p10 = tb10.text_frame.paragraphs[0]
    p10.text = "Day 5: Production Deployment, Load Test & 6-Week RCT Handover"
    p10.font.size = Pt(26)
    p10.font.bold = True
    p10.font.color.rgb = WHITE

    add_card(
        s10, 0.6, 3.1, 12.1, 3.6,
        "Production Stack & Next Steps for Ilm Academy",
        [
            "Docker Compose Stack: FastAPI RBAC backend (:8000) + Streamlit Teacher/Student App (:8501) + Isolated Sandbox + ChromaDB.",
            "Load Test Passed: 500 concurrent requests completed in 4.76s (105 req/s vs 0.83 req/s target) with 0.00% error rate.",
            "6-Week Randomized Controlled A/B Test: 163 students/arm (326 total) stratified by Week-1 ability to measure 45% -> 30% dropout reduction.",
            "Teacher Impact: ~200 teacher hours/week saved on 3,000 Sunday assignments, reinvested into 1-on-1 mentoring.",
        ],
        accent=EMERALD,
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    prs.save(OUT_PATH)
    print(f"Saved 10-slide widescreen presentation -> {OUT_PATH}")


if __name__ == "__main__":
    build_presentation()
