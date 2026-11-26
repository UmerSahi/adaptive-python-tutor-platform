# API Load Test & RBAC Verification Report

- **Target:** Live HTTP/TCP (http://127.0.0.1:8000)
- **Total Requests:** 500 (concurrent workers=8)
- **Total Wall Time:** 65.71 s
- **Throughput:** 7.6 req/s (well above 500 req / 10 min = 0.83 req/s target)
- **Error Rate:** 0.00% (0/500)
- **p50 Latency:** 1019.11 ms
- **p95 Latency:** 1215.62 ms
- **RBAC Check:** Student -> `/teacher/overview` = `403` (Denied), Teacher -> `/teacher/overview` = `200` (Allowed)
