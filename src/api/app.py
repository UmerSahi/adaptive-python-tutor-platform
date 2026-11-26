"""Ilm Academy FastAPI Backend with Role-Based Access Control (Day 5, Task 3):
Roles: student, teacher, admin
Endpoints:
- GET  /health
- POST /tutor/ask         (student, teacher, admin)
- POST /adaptive/next     (student, teacher, admin)
- POST /grade/submit      (student, teacher, admin)
- GET  /teacher/overview  (teacher, admin only)
"""

import json
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from src.adaptive.recommender import AdaptiveEngine
from src.grading.code_grader import grade_submission
from src.tutor.socratic_tutor import SocraticTutor

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUTS_DIR = BASE_DIR / "outputs"

API_KEYS = {
    "student-demo-key": "student",
    "teacher-demo-key": "teacher",
    "admin-demo-key": "admin",
}

app = FastAPI(title="Ilm Academy AI Tutor & Adaptive Learning API", version="1.0.0")

_tutor: SocraticTutor | None = None
_engine: AdaptiveEngine | None = None


def get_tutor() -> SocraticTutor:
    global _tutor
    if _tutor is None:
        _tutor = SocraticTutor()
    return _tutor


def get_engine() -> AdaptiveEngine:
    global _engine
    if _engine is None:
        _engine = AdaptiveEngine(seed=42)
    return _engine


def require_role(*allowed_roles: str):
    def _checker(x_api_key: str = Header(default=""), x_role: str = Header(default="")):
        role = API_KEYS.get(x_api_key) or x_role
        if role not in allowed_roles:
            raise HTTPException(status_code=403, detail=f"Access denied for role '{role}'. Required: {allowed_roles}")
        return role
    return _checker


class TutorRequest(BaseModel):
    message: str
    mastery_score: float = 0.4
    hint_stage: int = 1
    language: str = "en"


class AdaptiveRequest(BaseModel):
    ability: float = 0.0
    mastery: dict[str, float] = {}
    current_step: int = 0


class GradeRequest(BaseModel):
    code: str
    visible_tests: list[str]
    hidden_tests: list[str] = []
    lesson_id: str = "L06"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ilm-academy-api"}


@app.post("/tutor/ask")
def tutor_ask(req: TutorRequest, role: str = Depends(require_role("student", "teacher", "admin"))) -> dict[str, Any]:
    return get_tutor().respond(req.message, req.mastery_score, req.hint_stage, req.language)


@app.post("/adaptive/next")
def adaptive_next(req: AdaptiveRequest, role: str = Depends(require_role("student", "teacher", "admin"))) -> dict[str, Any]:
    rec = get_engine().recommend_next(req.ability, req.mastery, {}, req.current_step)
    return {
        "concept_id": rec["concept_id"],
        "question_id": rec["question"]["id"],
        "prompt": rec["question"]["prompt"],
        "predicted_success": rec["p_success"],
        "in_zpd": rec["in_zpd"],
    }


@app.post("/grade/submit")
def grade_submit(req: GradeRequest, role: str = Depends(require_role("student", "teacher", "admin"))) -> dict[str, Any]:
    return grade_submission(req.code, req.visible_tests, req.hidden_tests, req.lesson_id)


@app.get("/teacher/overview")
def teacher_overview(role: str = Depends(require_role("teacher", "admin"))) -> dict[str, Any]:
    profiles = pd.read_csv(DATA_DIR / "student_profiles.csv")
    interactions = pd.read_csv(DATA_DIR / "learner_interactions.csv")
    return {
        "total_students": int(len(profiles)),
        "total_interactions": int(len(interactions)),
        "mean_accuracy": round(float(interactions["correct"].mean()), 4),
        "pre_week4_dropout_rate": round(float(((profiles["dropped_out"] == 1) & (profiles["dropout_week"] < 4)).mean()), 4),
    }
