"""Build a clean venv, install the wheel, and run imports/README examples outside the checkout."""

import os
import subprocess
import sys
import tempfile
import venv
import zipfile
from pathlib import Path


def main():
    wheel = Path(sys.argv[1]).resolve()
    root = Path(__file__).resolve().parents[1]
    with zipfile.ZipFile(wheel) as archive:
        assert "ta_config/py.typed" in archive.namelist()
    snippets = []
    for block in (root / "README.md").read_text(encoding="utf-8-sig").split("```python\n")[1:]:
        snippets.append(block.split("```", 1)[0])
    with tempfile.TemporaryDirectory(prefix="ta-config-wheel-") as directory:
        directory = Path(directory)
        venv.EnvBuilder(with_pip=True).create(directory / "venv")
        python = directory / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        env = dict(os.environ)
        env.pop("PYTHONPATH", None)
        subprocess.run(
            [str(python), "-m", "pip", "install", str(wheel)], cwd=directory, env=env, check=True
        )
        code = (
            "from pathlib import Path\nimport ta_config\n"
            f"assert not Path(ta_config.__file__).is_relative_to({str(root)!r})\n"
            "from ta_config import RelativePosition, StreamEngine, SMACalcConfig\n"
            + "\n".join(snippets)
        )
        subprocess.run([str(python), "-c", code], cwd=directory, env=env, check=True)
    print("Clean wheel imports, typing marker, and README examples passed.")


if __name__ == "__main__":
    main()
