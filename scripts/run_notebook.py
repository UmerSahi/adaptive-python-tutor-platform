"""Execute all code cells in notebooks/eda_analytics.ipynb, capture stdout and matplotlib PNGs,
and save outputs cleanly in-place with zero warnings."""

import base64
import contextlib
import io
import json
import os
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent.parent
NB_PATH = BASE_DIR / "notebooks" / "eda_analytics.ipynb"


def main():
    nb = json.loads(NB_PATH.read_text(encoding="utf-8"))
    ns: dict = {}
    orig_cwd = os.getcwd()
    os.chdir(NB_PATH.parent)

    captured_images: list[str] = []

    def _custom_show(*args, **kwargs):
        for fignum in plt.get_fignums():
            fig = plt.figure(fignum)
            img_buf = io.BytesIO()
            fig.savefig(img_buf, format="png", bbox_inches="tight", dpi=130)
            img_buf.seek(0)
            captured_images.append(base64.b64encode(img_buf.read()).decode("ascii"))
        plt.close("all")

    plt.show = _custom_show

    try:
        exec_count = 1
        for cell in nb["cells"]:
            if cell["cell_type"] != "code":
                continue
            code = "".join(cell["source"])
            buf = io.StringIO()
            captured_images.clear()
            with warnings.catch_warnings():
                warnings.simplefilter("error")  # Fail if any warning remains!
                with contextlib.redirect_stdout(buf):
                    exec(compile(code, str(NB_PATH), "exec"), ns)

            out_text = buf.getvalue()
            cell["execution_count"] = exec_count
            exec_count += 1
            outputs = []
            if out_text:
                outputs.append(
                    {
                        "name": "stdout",
                        "output_type": "stream",
                        "text": [line + "\n" for line in out_text.splitlines()],
                    }
                )
            for b64 in captured_images:
                outputs.append(
                    {
                        "data": {"image/png": b64, "text/plain": ["<Figure>"]},
                        "metadata": {},
                        "output_type": "display_data",
                    }
                )
            cell["outputs"] = outputs
            if out_text:
                print(out_text, end="")
    finally:
        os.chdir(orig_cwd)

    NB_PATH.write_text(json.dumps(nb, indent=2), encoding="utf-8")
    print(f"\nExecuted cleanly (0 warnings, 0 errors) and embedded all figures -> {NB_PATH}")


if __name__ == "__main__":
    main()
