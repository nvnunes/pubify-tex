from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path
import sys

import matplotlib
import numpy as np
from mpl_toolkits.axes_grid1 import make_axes_locatable

matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = REPO_ROOT / "src"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from pubify_tex import DEFAULT_TEMPLATE, prepare, save_fig, use_template


GALLERY_SOURCE_DIR = REPO_ROOT / "gallery"
DEBUG_SOURCE_DIR = REPO_ROOT / "debug"
SOURCE_ROOTS = (GALLERY_SOURCE_DIR, DEBUG_SOURCE_DIR)
BUILD_DIR = REPO_ROOT / "build" / "tex"
DEFAULT_TEX_FILE = "gallery/layout-gallery.tex"
TEX_INCLUDE_RE = re.compile(r"\\(?:input|include)\{([^}]+)\}")

PUBIFY_TEMPLATE = DEFAULT_TEMPLATE.copy()


def make_sample_image_fig():
    n = 400
    x = np.linspace(-5, 5, n)
    y = np.linspace(-5, 5, n)
    x_grid, y_grid = np.meshgrid(x, y)
    radius = np.sqrt(x_grid**2 + y_grid**2)
    values = np.sinc(radius)

    fig, ax = plt.subplots(figsize=(5, 4))
    image = ax.imshow(
        values,
        extent=[x.min(), x.max(), y.min(), y.max()],
        origin="lower",
        cmap="cividis",
    )
    ax.set_aspect("equal")
    ax.set_title("Example Image Plot")
    ax.set_xlabel("X coordinate")
    ax.set_ylabel("Y coordinate")

    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.05)
    colorbar = fig.colorbar(image, cax=cax)
    colorbar.set_label("Intensity")
    plt.sca(ax)
    fig.tight_layout()
    return fig


def make_sample_plot_fig():
    radius = np.linspace(0, 10, 300)
    profile = np.exp(-0.3 * radius) * (1 + 0.3 * np.sin(4 * radius))

    fig, ax = plt.subplots(figsize=(7, 3))
    ax.plot(radius, profile)
    ax.set_xlabel("Radius")
    ax.set_ylabel("Signal")
    ax.grid(True)
    fig.tight_layout()
    return fig


def reset_build_dir():
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR, ignore_errors=True)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)


def _source_root_for(path: Path) -> Path:
    for root in SOURCE_ROOTS:
        root_resolved = root.resolve()
        if path == root_resolved or root_resolved in path.parents:
            return root
    raise ValueError("Path must refer to a file inside gallery/ or debug/")


def resolve_tex_source(tex_file: str) -> Path:
    candidate = Path(tex_file)
    if candidate.is_absolute():
        raise ValueError("tex_file must be relative to gallery/ or debug/")

    source_path = (REPO_ROOT / candidate).resolve()
    _source_root_for(source_path)
    if source_path.suffix != ".tex":
        raise ValueError("tex_file must be a .tex file")
    if not source_path.exists():
        raise FileNotFoundError(source_path)
    return source_path


def _strip_tex_comments(text: str) -> str:
    lines = []
    for line in text.splitlines():
        parts = re.split(r"(?<!\\)%", line, maxsplit=1)
        lines.append(parts[0])
    return "\n".join(lines)


def _resolve_local_include(base_dir: Path, include_target: str) -> Path:
    candidate = Path(include_target)
    if candidate.is_absolute():
        raise ValueError("TeX includes must be relative to gallery/ or debug/")
    if candidate.suffix == "":
        candidate = candidate.with_suffix(".tex")

    source_path = (base_dir / candidate).resolve()
    _source_root_for(source_path)
    if not source_path.exists():
        raise FileNotFoundError(source_path)
    return source_path


def collect_tex_sources(tex_file: str) -> list[Path]:
    root = resolve_tex_source(tex_file)
    collected: list[Path] = []
    seen: set[Path] = set()

    def visit(source_path: Path) -> None:
        if source_path in seen:
            return
        seen.add(source_path)
        collected.append(source_path)

        text = _strip_tex_comments(source_path.read_text())
        for include_target in TEX_INCLUDE_RE.findall(text):
            visit(_resolve_local_include(source_path.parent, include_target))

    visit(root)
    return collected


def _staged_tex_names(source_paths: list[Path]) -> dict[Path, str]:
    names: dict[str, Path] = {}
    staged: dict[Path, str] = {}
    for source_path in source_paths:
        name = source_path.name
        existing = names.get(name)
        if existing is not None and existing != source_path:
            raise ValueError(f"TeX source basename collision: {existing} and {source_path}")
        names[name] = source_path
        staged[source_path] = name
    return staged


def _rewrite_tex_source(text: str, source_path: Path, staged_names: dict[Path, str]) -> str:
    def replace_include(match: re.Match[str]) -> str:
        include_target = match.group(1)
        included_path = _resolve_local_include(source_path.parent, include_target)
        staged_name = staged_names.get(included_path)
        if staged_name is None:
            return match.group(0)
        command = match.group(0).split("{", 1)[0]
        return f"{command}{{{Path(staged_name).with_suffix('').name}}}"

    rewritten = TEX_INCLUDE_RE.sub(replace_include, text)
    rewritten = rewritten.replace(r"\graphicspath{{../}}", r"\graphicspath{{./}}")
    return rewritten


def write_tex_sources(tex_file: str):
    source_paths = collect_tex_sources(tex_file)
    staged_names = _staged_tex_names(source_paths)
    for source_path in source_paths:
        destination = BUILD_DIR / staged_names[source_path]
        text = source_path.read_text()
        destination.write_text(_rewrite_tex_source(text, source_path, staged_names))
    prepare(BUILD_DIR, template=PUBIFY_TEMPLATE)
    return BUILD_DIR / staged_names[resolve_tex_source(tex_file)]


def write_figures():
    fig_img = make_sample_image_fig()
    fig_plot = make_sample_plot_fig()

    with use_template(PUBIFY_TEMPLATE):
        save_fig(fig_img, "one", BUILD_DIR / "fig-example-one.pdf", caption_lines=4)
        save_fig(fig_plot, "one", BUILD_DIR / "fig-example-one-high.pdf", caption_lines=4)
        save_fig(fig_plot, "onewide", BUILD_DIR / "fig-example-onewide.pdf", caption_lines=4)
        save_fig(fig_plot, "twowide", BUILD_DIR / "fig-example-twowide-1.pdf", caption_lines=4)
        save_fig(
            fig_plot,
            "twowide",
            BUILD_DIR / "fig-example-twowide-1-subcaptions.pdf",
            caption_lines=4,
            subcaption_lines=1,
        )
        save_fig(fig_plot, "twowide", BUILD_DIR / "fig-example-twowide-2.pdf", caption_lines=4)
        save_fig(
            fig_plot,
            "twowide",
            BUILD_DIR / "fig-example-twowide-2-subcaptions.pdf",
            caption_lines=4,
            subcaption_lines=1,
        )
        save_fig(fig_img, "two", BUILD_DIR / "fig-example-two-1.pdf", caption_lines=4)
        save_fig(fig_plot, "two", BUILD_DIR / "fig-example-two-2.pdf", caption_lines=4)
        save_fig(
            fig_plot,
            "two",
            BUILD_DIR / "fig-example-two-2-subcaptions.pdf",
            caption_lines=4,
            subcaption_lines=1,
        )
        save_fig(
            fig_plot,
            "two",
            BUILD_DIR / "fig-example-two-2-fixedaspect.pdf",
            caption_lines=4,
            force_aspect=0.62,
        )
        save_fig(fig_img, "three", BUILD_DIR / "fig-example-three-1.pdf", caption_lines=4)
        save_fig(fig_plot, "three", BUILD_DIR / "fig-example-three-2.pdf", caption_lines=4)
        save_fig(
            fig_plot,
            "three",
            BUILD_DIR / "fig-example-three-2-fixedaspect.pdf",
            caption_lines=4,
            force_aspect=0.62,
        )
        save_fig(fig_plot, "threewide", BUILD_DIR / "fig-example-threewide.pdf", caption_lines=4)
        save_fig(
            fig_plot,
            "threewide",
            BUILD_DIR / "fig-example-threewide-subcaptions.pdf",
            caption_lines=4,
            subcaption_lines=1,
        )
        save_fig(fig_img, "four", BUILD_DIR / "fig-example-four-1.pdf", caption_lines=4)
        save_fig(fig_plot, "four", BUILD_DIR / "fig-example-four-2.pdf", caption_lines=4)
        save_fig(
            fig_plot,
            "four",
            BUILD_DIR / "fig-example-four-2-subcaptions.pdf",
            caption_lines=4,
            subcaption_lines=1,
        )
        save_fig(fig_img, "six", BUILD_DIR / "fig-example-six-1.pdf", caption_lines=4)
        save_fig(fig_plot, "six", BUILD_DIR / "fig-example-six-2.pdf", caption_lines=4)
        save_fig(fig_plot, "sixwide", BUILD_DIR / "fig-example-sixwide.pdf", caption_lines=4)
        save_fig(
            fig_img,
            "nine",
            BUILD_DIR / "fig-example-nine-1.pdf",
            caption_lines=4,
            hide_labels=True,
            hide_ticks=True,
            hide_cbar=True,
        )
        save_fig(
            fig_plot,
            "nine",
            BUILD_DIR / "fig-example-nine-2.pdf",
            caption_lines=4,
            hide_labels=True,
            hide_ticks=True,
            hide_cbar=True,
        )
        save_fig(
            fig_plot,
            "twelve",
            BUILD_DIR / "fig-example-twelve.pdf",
            caption_lines=4,
            hide_labels=True,
            hide_ticks=True,
            hide_cbar=True,
        )
        save_fig(
            fig_plot,
            "twelvewide",
            BUILD_DIR / "fig-example-twelvewide.pdf",
            caption_lines=4,
            hide_labels=True,
            hide_ticks=True,
            hide_cbar=True,
        )
        save_fig(
            fig_plot,
            "fifteen",
            BUILD_DIR / "fig-example-fifteen.pdf",
            caption_lines=4,
            hide_labels=True,
            hide_ticks=True,
            hide_cbar=True,
        )
        save_fig(
            fig_plot,
            "sixteen",
            BUILD_DIR / "fig-example-sixteen.pdf",
            caption_lines=4,
            hide_labels=True,
            hide_ticks=True,
            hide_cbar=True,
        )
        save_fig(
            fig_plot,
            "twenty",
            BUILD_DIR / "fig-example-twenty.pdf",
            caption_lines=4,
            hide_labels=True,
            hide_ticks=True,
            hide_cbar=True,
        )

    plt.close(fig_img)
    plt.close(fig_plot)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage a self-contained pubify TeX workspace.")
    parser.add_argument(
        "tex_file",
        nargs="?",
        default=DEFAULT_TEX_FILE,
        help=f"TeX file from gallery/ or debug/ to stage (default: {DEFAULT_TEX_FILE})",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None):
    args = parse_args([] if argv is None else argv)
    reset_build_dir()
    staged_tex_file = write_tex_sources(args.tex_file)
    write_figures()
    print(f"TeX workspace written to {BUILD_DIR}")
    print(f"Staged TeX file: {staged_tex_file}")
    print(f"Built artifacts: {BUILD_DIR}")


if __name__ == "__main__":
    main(sys.argv[1:])
