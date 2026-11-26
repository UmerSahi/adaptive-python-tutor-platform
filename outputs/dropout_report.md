# Dropout Early-Warning Model Report (LightGBM + SHAP)

- **Test Students:** 250 (Pre-Week-4 dropout prevalence: 40.4%)
- **PR-AUC:** 0.9183
- **ROC-AUC:** 0.9102

## Top SHAP Drivers
- `concepts_covered`: mean |SHAP| = 2.2858
- `early_attempts`: mean |SHAP| = 0.8265
- `early_accuracy`: mean |SHAP| = 0.6638
- `std_rt_sec`: mean |SHAP| = 0.3593
- `avg_rt_sec`: mean |SHAP| = 0.2802
- `fast_wrong_rate`: mean |SHAP| = 0.1720
- `max_attempt_on_concept`: mean |SHAP| = 0.0000

## Risk Tiers & Intervention Actions
- **High (>= 0.60)** (92 students): Trigger 1-on-1 mentor check-in, switch to scaffolded ZPD review, send UrduLish encouragement.
- **Medium (0.35 - 0.59)** (14 students): Insert spaced-repetition refresher + Socratic hint prompts on prerequisite gaps.
- **Low (< 0.35)** (144 students): Continue adaptive ZPD path with standard spaced repetition.
