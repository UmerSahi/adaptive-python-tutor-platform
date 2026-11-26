# Impact Evaluation & A/B Test Design

## 1. Simulated Impact: Adaptive vs. Fixed Curriculum
- **Learning Gain:** `0.0703` vs `0.0488` (**+44.1%** lift)
- **ZPD Hit Rate (60-80% success):** `71.0%` vs `31.3%`
- **Prerequisite Violations:** `0.0%` vs `93.3%`
- **Projected Pre-Week-4 Dropout:** Reduced from `45.0%` baseline toward `~28-30%` via early-warning interventions + ZPD scaffolding.
- **Teacher Time Saved:** Auto-grading `3,000` Sunday assignments saves **~200.0 teacher hours/week** (at 4 min/assignment), shifting teachers to high-value mentoring.

## 2. Randomized Controlled A/B Test Design
- **Randomization Unit:** Student-level (50/50 stratified by Week-1 diagnostic ability).
- **Arms:** Control = Fixed linear path; Treatment = Adaptive ZPD + Spaced Repetition + Socratic Tutor + Dropout Early-Warning.
- **Sample Size:** **163 students per arm** (326 total) for 80% power at alpha=0.05 to detect a 15pp dropout reduction (45% -> 30%).
- **Duration:** 6 weeks (full Python module).
- **Primary Metrics:** Pre-Week-4 dropout rate, post-test mastery gain, time-to-mastery.
- **Guardrail Metrics:** Tutor answer leakage (`0%` target), grading latency (`< 2s`), student satisfaction.
