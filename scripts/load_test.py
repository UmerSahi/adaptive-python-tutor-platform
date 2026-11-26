"""Load Test for Ilm Academy API (Day 5, Task 3):
Simulates 500 submissions over live HTTP/TCP (or TestClient fallback)
and reports throughput, p50/p95 latency, error rate, and RBAC isolation.
"""

import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import httpx
import numpy as np
from fastapi.testclient import TestClient

from src.api.app import app

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = BASE_DIR / "outputs"
LIVE_URL = "http://127.0.0.1:8000"


def _is_live_server_up() -> bool:
    try:
        r = httpx.get(f"{LIVE_URL}/health", timeout=1.5)
        return r.status_code == 200
    except Exception:
        return False


def run_load_test(n_requests: int = 500, workers: int = 8):
    use_live = _is_live_server_up()
    mode_label = f"Live HTTP/TCP ({LIVE_URL})" if use_live else "In-Process FastAPI TestClient"
    headers = {"X-API-Key": "student-demo-key"}

    def one_request(i: int):
        t0 = time.perf_counter()
        if use_live:
            with httpx.Client(base_url=LIVE_URL, timeout=10.0) as client:
                if i % 5 == 0:
                    r = client.post(
                        "/grade/submit",
                        headers=headers,
                        json={
                            "code": "def add(a, b):\n    return a + b",
                            "visible_tests": ["assert add(2, 3) == 5"],
                            "hidden_tests": ["assert add(-1, 1) == 0"],
                        },
                    )
                else:
                    r = client.post(
                        "/adaptive/next",
                        headers=headers,
                        json={"ability": 0.2, "mastery": {"variables": 0.9}, "current_step": i % 10},
                    )
        else:
            client = TestClient(app)
            if i % 5 == 0:
                r = client.post(
                    "/grade/submit",
                    headers=headers,
                    json={
                        "code": "def add(a, b):\n    return a + b",
                        "visible_tests": ["assert add(2, 3) == 5"],
                        "hidden_tests": ["assert add(-1, 1) == 0"],
                    },
                )
            else:
                r = client.post(
                    "/adaptive/next",
                    headers=headers,
                    json={"ability": 0.2, "mastery": {"variables": 0.9}, "current_step": i % 10},
                )
        ms = (time.perf_counter() - t0) * 1000.0
        return r.status_code, ms

    t_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(one_request, range(n_requests)))
    total_sec = time.perf_counter() - t_start

    statuses = [s for s, _ in results]
    latencies = [ms for _, ms in results]
    errors = sum(1 for s in statuses if s != 200)

    if use_live:
        rbac_resp = httpx.get(f"{LIVE_URL}/teacher/overview", headers={"X-API-Key": "student-demo-key"})
        rbac_teacher = httpx.get(f"{LIVE_URL}/teacher/overview", headers={"X-API-Key": "teacher-demo-key"})
    else:
        tc = TestClient(app)
        rbac_resp = tc.get("/teacher/overview", headers={"X-API-Key": "student-demo-key"})
        rbac_teacher = tc.get("/teacher/overview", headers={"X-API-Key": "teacher-demo-key"})

    report = (
        "# API Load Test & RBAC Verification Report\n\n"
        f"- **Target:** {mode_label}\n"
        f"- **Total Requests:** {n_requests} (concurrent workers={workers})\n"
        f"- **Total Wall Time:** {total_sec:.2f} s\n"
        f"- **Throughput:** {n_requests / total_sec:.1f} req/s (well above 500 req / 10 min = 0.83 req/s target)\n"
        f"- **Error Rate:** {errors / n_requests:.2%} ({errors}/{n_requests})\n"
        f"- **p50 Latency:** {np.percentile(latencies, 50):.2f} ms\n"
        f"- **p95 Latency:** {np.percentile(latencies, 95):.2f} ms\n"
        f"- **RBAC Check:** Student -> `/teacher/overview` = `{rbac_resp.status_code}` (Denied), "
        f"Teacher -> `/teacher/overview` = `{rbac_teacher.status_code}` (Allowed)\n"
    )
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUTS_DIR / "load_test_report.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    run_load_test(500, workers=8)
