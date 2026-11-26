# API Load Test & RBAC Verification Report

- **Total Requests:** 500 (concurrent workers=8)
- **Total Wall Time:** 4.76 s
- **Throughput:** 105.0 req/s (well above 500 req / 10 min = 0.83 req/s target)
- **Error Rate:** 0.00% (0/500)
- **p50 Latency:** 17.37 ms
- **p95 Latency:** 148.26 ms
- **RBAC Check:** Student -> `/teacher/overview` = `403` (Denied), Teacher -> `/teacher/overview` = `200` (Allowed)
