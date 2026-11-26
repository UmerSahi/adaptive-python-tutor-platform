"""Execute all code cells in notebooks/eda_analytics.ipynb and save outputs in-place."""

import contextlib
import io
import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
NB_PATH = BASE_DIR / "notebooks" / "eda_analytics.ipynb"


def main():
    nb = json.loads(NB_PATH.read_text(encoding="utf-8"))
    ns: dict = {}
    orig_cwd = os.getcwd()
    os.chdir(NB_PATH.parent)

    # Use non-interactive matplotlib backend
    import matplotlib
    matplotlib.use("Agg")

    try:
        exec_count = 1
        for cell in nb["cells"]:
            if cell["cell_type"] != "code":
                continue
            code = "".join(cell["source"])
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                exec(compile(code, str(NB_PATH), "exec"), ns)
            out_text = buf.getvalue()
            cell["execution_count"] = exec_count
            exec_count += 1
            cell["outputs"] = (
                [
                    {
                        "name": "stdout",
                        "output_type": "stream",
                        "text": [line + "\n" for line in out_text.splitlines()],
                    }
                ]
                if out_text
                else []
            )
            if out_text:
                print(out_text, end="")
    finally:
        os.chdir(orig_cwd)

    NB_PATH.write_text(json.dumps(nb, indent=2), encoding="utf-8")
    print(f"\nExecuted and saved {NB_PATH}")


if __name__ == "__main__":
    main()
