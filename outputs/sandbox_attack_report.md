# Sandbox Security Attack Report

Controls: AST static import/builtin blocklist + `python -I` isolated subprocess + scrubbed env + 1.5s–2.0s timeout (paired with `Dockerfile.sandbox` `--network=none --cpus=0.5 --memory=128m --pids-limit=32`).

| Attack Vector | Result Status | Defended | Elapsed (ms) | Detail |
| :--- | :---: | :---: | :---: | :--- |
| Infinite Loop | `timeout` | True | 1512.03 | Execution timed out after 1.5s limit. |
| Fork Bomb | `blocked` | True | 0.0 | Blocked import: 'os' is not permitted in sandbox. |
| Environment Secret Access | `blocked` | True | 0.0 | Blocked import: 'os' is not permitted in sandbox. |
| Network Exfiltration | `blocked` | True | 0.0 | Blocked import: 'socket' is not permitted in sandbox. |
| File System Write | `blocked` | True | 0.0 | Blocked builtin call: 'open()' is not permitted in sandbox. |
| Dynamic Import Evasion | `blocked` | True | 0.0 | Blocked builtin call: '__import__()' is not permitted in sandbox. |
| Dunder Reflection Escape | `blocked` | True | 0.0 | Blocked reflection attribute: '__subclasses__' is not permitted in sandbox. |
| Builtins Getattr Bypass | `blocked` | True | 0.0 | Blocked builtin call: 'getattr()' is not permitted in sandbox. |
