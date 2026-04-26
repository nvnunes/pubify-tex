from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
GALLERY_DIR = REPO_ROOT / "gallery"
BUILD_DIR = REPO_ROOT / "build" / "tex"
OUTPUT_PDF = GALLERY_DIR / "layout-gallery.pdf"


def run(cmd: list[str], *, cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> None:
    run([sys.executable, "scripts/build_tex_assets.py", "gallery/layout-gallery.tex"], cwd=REPO_ROOT)
    run(
        ["latexmk", "-g", "-pdf", "-interaction=nonstopmode", "layout-gallery.tex"],
        cwd=BUILD_DIR,
    )
    shutil.copy(BUILD_DIR / "layout-gallery.pdf", OUTPUT_PDF)
    print(f"Updated gallery PDF at {OUTPUT_PDF}")


if __name__ == "__main__":
    main()
