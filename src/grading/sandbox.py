"""Secure Python Code Sandbox (Day 4, Task 1):
- AST static security analyzer blocking dangerous imports/builtins (os, subprocess, socket, open, eval, exec, __import__)
- Isolated subprocess execution with strict CPU/wall-clock timeout (2.0s), scrubbed environment, and output cap
- Attack test suite verifying defense against infinite loops, fork bombs, env access, network, file I/O, and evasion
"""

import ast
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUTS_DIR = BASE_DIR / "outputs"

BLOCKED_MODULES = {
    "os", "sys", "subprocess", "socket", "urllib", "requests", "http",
    "shutil", "pathlib", "ctypes", "multiprocessing", "threading", "pty", "resource",
}
BLOCKED_BUILTINS = {
    "eval", "exec", "compile", "open", "__import__", "breakpoint", "input",
    "getattr", "setattr", "delattr", "globals", "locals", "vars", "dir",
}
BLOCKED_DUNDER_ATTRS = {
    "__subclasses__", "__globals__", "__builtins__", "__import__",
    "__loader__", "__code__", "__class__", "__bases__", "__mro__",
}


def check_ast_security(code: str) -> tuple[bool, str]:
    """Statically inspect Python AST for disallowed imports, builtins, or dunder reflection escapes."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return False, f"SyntaxError: {exc.msg} (line {exc.lineno})"

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in BLOCKED_MODULES:
                    return False, f"Blocked import: '{root}' is not permitted in sandbox."
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root in BLOCKED_MODULES:
                return False, f"Blocked import-from: '{root}' is not permitted in sandbox."
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in BLOCKED_BUILTINS:
                return False, f"Blocked builtin call: '{node.func.id}()' is not permitted in sandbox."
        elif isinstance(node, ast.Attribute) and node.attr in BLOCKED_DUNDER_ATTRS:
            return False, f"Blocked reflection attribute: '{node.attr}' is not permitted in sandbox."
        elif isinstance(node, ast.Name) and node.id in BLOCKED_DUNDER_ATTRS:
            return False, f"Blocked reflection name: '{node.id}' is not permitted in sandbox."
    return True, "OK"


def run_in_sandbox(code: str, timeout_sec: float = 2.0, max_output_chars: int = 4096) -> dict[str, Any]:
    """Execute untrusted Python code in a scrubbed, time-limited subprocess."""
    safe, reason = check_ast_security(code)
    if not safe:
        return {
            "status": "blocked",
            "passed": False,
            "stdout": "",
            "stderr": reason,
            "elapsed_ms": 0.0,
        }

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(code)
        tmp_path = tmp.name

    # Scrubbed minimal environment so host secrets/tokens cannot be read
    scrubbed_env = {
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", r"C:\Windows"),
    }

    t0 = time.perf_counter()
    try:
        proc = subprocess.run(
            [sys.executable, "-I", tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            env=scrubbed_env,
        )
        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        return {
            "status": "ok" if proc.returncode == 0 else "runtime_error",
            "passed": proc.returncode == 0,
            "stdout": proc.stdout[:max_output_chars],
            "stderr": proc.stderr[:max_output_chars],
            "elapsed_ms": elapsed_ms,
        }
    except subprocess.TimeoutExpired:
        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        return {
            "status": "timeout",
            "passed": False,
            "stdout": "",
            "stderr": f"Execution timed out after {timeout_sec}s limit.",
            "elapsed_ms": elapsed_ms,
        }
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def run_attack_suite() -> list[dict[str, Any]]:
    """Test sandbox against 6 malicious code patterns and write attack report."""
    attacks = [
        ("Infinite Loop", "while True:\n    pass"),
        ("Fork Bomb", "import os\nwhile True:\n    os.fork()"),
        ("Environment Secret Access", "import os\nprint(dict(os.environ))"),
        ("Network Exfiltration", "import socket\ns = socket.socket()\ns.connect(('1.1.1.1', 80))"),
        ("File System Write", "open('pwned.txt', 'w').write('hacked')"),
        ("Dynamic Import Evasion", "__import__('os').system('whoami')"),
        ("Dunder Reflection Escape", "().__class__.__bases__[0].__subclasses__()"),
        ("Builtins Getattr Bypass", "getattr(__builtins__, 'open')('secret.txt')"),
    ]

    results = []
    for name, payload in attacks:
        res = run_in_sandbox(payload, timeout_sec=1.5)
        defended = res["status"] in {"blocked", "timeout"}
        results.append(
            {
                "attack": name,
                "status": res["status"],
                "defended": defended,
                "elapsed_ms": res["elapsed_ms"],
                "detail": res["stderr"].strip(),
            }
        )

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Sandbox Security Attack Report\n",
        "Controls: AST static import/builtin blocklist + `python -I` isolated subprocess + scrubbed env + 1.5s–2.0s timeout (paired with `Dockerfile.sandbox` `--network=none --cpus=0.5 --memory=128m --pids-limit=32`).\n",
        "| Attack Vector | Result Status | Defended | Elapsed (ms) | Detail |",
        "| :--- | :---: | :---: | :---: | :--- |",
    ]
    for r in results:
        lines.append(f"| {r['attack']} | `{r['status']}` | {r['defended']} | {r['elapsed_ms']} | {r['detail']} |")

    (OUTPUTS_DIR / "sandbox_attack_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return results


if __name__ == "__main__":
    run_attack_suite()
