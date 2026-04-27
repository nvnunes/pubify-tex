from __future__ import annotations

from pathlib import Path
from typing import Any

from matplotlib.axes import Axes
from matplotlib.figure import Figure

from pubify_mpl import (
    ResolvedStyle,
    auto_rasterize_figure,
    figure_tight_bbox,
    prepare_figure,
)

from .layout import latex_layout_geometry, matplotlib_style_from_template, normalized_template


PUBIFY_LATEX_PREAMBLE = r"""
\usepackage[T1]{fontenc}
\usepackage[tracking]{microtype}
\usepackage{amsmath}
\usepackage{amssymb}
"""
PUBIFY_TEX_FONT_FAMILY = "serif"
PUBIFY_TEX_FONT_SERIF = ["Latin Modern Roman", "LMRoman10"]
PUBIFY_TEX_MATHTEXT_FONTSET = "cm"


def save_fig(
    fig_or_ax: Figure | Axes,
    layout: str,
    filename: str | Path,
    *,
    template: dict[str, Any] | None = None,
    caption_lines: int | None = None,
    subcaption_lines: int | None = None,
    force_width: float | None = None,
    force_height: float | None = None,
    force_aspect: float | None = None,
    dpi: int = 300,
    keep_titles: bool = False,
    hide_labels: bool = False,
    hide_annotations: bool = False,
    hide_ticks: bool = False,
    hide_tick_labels: bool = False,
    hide_grid: bool = False,
    hide_cbar: bool = False,
    skip_clone: bool = False,
    skip_rasterize: bool = False,
    rasterize_scatter_threshold: int = 1000,
    rasterize_image_pixel_threshold: int = 1_000_000,
    rasterize_line_vertex_threshold: int = 2000,
    extra_rcparams: dict[str, Any] | None = None,
    prepare_export: object | None = None,
    verbose: bool = False,
) -> None:
    """Export a Matplotlib figure or axes for a named LaTeX layout."""

    resolved_template = normalized_template(template)

    if caption_lines is None:
        caption_lines = 1
    caption_lines = int(caption_lines)
    if caption_lines < 0:
        raise ValueError("caption_lines must be non-negative.")

    if subcaption_lines is None:
        subcaption_lines = 0
    subcaption_lines = int(subcaption_lines)
    if subcaption_lines < 0:
        raise ValueError("subcaption_lines must be non-negative.")

    if force_width is not None and force_height is not None:
        raise ValueError("force_width and force_height are mutually exclusive.")
    if isinstance(force_width, str):
        raise ValueError("force_width must be a float in inches.")
    if force_height is not None:
        force_height = float(force_height)
        if force_height <= 0.0:
            raise ValueError("force_height must be positive.")

    output_filename = Path(filename).expanduser()
    if not output_filename.suffix:
        output_filename = output_filename.with_suffix(".pdf")
    parent_dir = output_filename.parent
    if output_filename.is_absolute():
        if not parent_dir.exists():
            raise FileNotFoundError(
                f"Parent directory does not exist for output file: {output_filename}"
            )
    else:
        parent_dir.mkdir(parents=True, exist_ok=True)

    export_rcparams = {
        "font.serif": list(PUBIFY_TEX_FONT_SERIF),
        "mathtext.fontset": PUBIFY_TEX_MATHTEXT_FONTSET,
        "text.latex.preamble": PUBIFY_LATEX_PREAMBLE,
    }
    if extra_rcparams:
        export_rcparams.update(extra_rcparams)

    with prepare_figure(
        fig_or_ax,
        style=matplotlib_style_from_template(resolved_template),
        dpi=dpi,
        keep_titles=keep_titles,
        hide_labels=hide_labels,
        hide_annotations=hide_annotations,
        hide_ticks=hide_ticks,
        hide_tick_labels=hide_tick_labels,
        hide_grid=hide_grid,
        hide_cbar=hide_cbar,
        skip_clone=skip_clone,
        extra_rcparams=export_rcparams,
        text_usetex=True,
        font_family=PUBIFY_TEX_FONT_FAMILY,
        prepare_export=prepare_export,  # type: ignore[arg-type]
    ) as fig_export:
        bbox = figure_tight_bbox(fig_export)

        preserve_composite_aspect = False
        if force_aspect is not None:
            force_aspect = float(force_aspect)
        elif isinstance(fig_or_ax, Figure):
            force_aspect = bbox.height / bbox.width
            preserve_composite_aspect = True
        else:
            fig_aspect = fig_export.axes[0].get_aspect()
            if fig_aspect in {"equal", 1.0}:
                force_aspect = 1.0
            elif fig_aspect != "auto":
                force_aspect = float(fig_aspect)

        if not isinstance(layout, str):
            raise TypeError(
                "layout must be a named layout string. "
                "Use force_width=... or force_height=... to constrain the export."
            )

        layout_geometry = latex_layout_geometry(
            layout=layout,
            layout_spec=resolved_template,
            caption_lines=caption_lines,
            subcaption_lines=subcaption_lines,
        )
        layout_width = layout_geometry["width_in"]
        layout_height = layout_geometry["height_in"]
        wide_layout = layout in {"onewide", "twowide", "threewide"}

        if wide_layout:
            if force_width is not None:
                raise ValueError(
                    "force_width is not supported for layouts "
                    "'onewide', 'twowide', and 'threewide'. "
                    "Wide layouts always use the full layout width."
                )
            width = layout_width
            if force_aspect is None:
                force_aspect = bbox.height / bbox.width
            height = width if force_aspect == 1.0 else width * force_aspect
        elif force_width is None:
            if force_aspect == 1.0:
                width = layout_width
                height = layout_height
            elif force_aspect is not None:
                target_width = layout_height / force_aspect
                target_height = layout_width * force_aspect
                if target_width > layout_width:
                    width = layout_width
                    height = target_height
                else:
                    width = target_width
                    height = layout_height
            else:
                width = layout_width
                height = layout_height
        else:
            width = float(force_width)
            if width > layout_width + 1e-9:
                raise ValueError(
                    f"force_width={width:.5f}in exceeds the available width "
                    f"for layout '{layout}' ({layout_width:.5f}in)."
                )
            if force_aspect is None:
                force_aspect = bbox.height / bbox.width
            height = width if force_aspect == 1.0 else width * force_aspect
            if height > layout_height + 1e-9:
                raise ValueError(
                    f"force_width={width:.5f}in with force_aspect {force_aspect:.5f} "
                    f"produces height {height:.5f}in, which exceeds the "
                    f"available height for layout '{layout}' ({layout_height:.5f}in)."
                )

        if force_height is not None and height > force_height + 1e-9:
            scale = force_height / height
            width *= scale
            height *= scale

        for _ in range(10):
            if preserve_composite_aspect:
                scale = min(width / bbox.width, height / bbox.height)
                if abs(scale - 1.0) < 0.005:
                    break
                current_w, current_h = fig_export.get_size_inches()
                fig_export.set_size_inches(current_w * scale, current_h * scale, forward=True)
            else:
                wscale = width / bbox.width
                hscale = height / bbox.height
                if abs(wscale - 1.0) < 0.005 and abs(hscale - 1.0) < 0.005:
                    break
                current_w, current_h = fig_export.get_size_inches()
                fig_export.set_size_inches(
                    current_w * wscale,
                    current_h * hscale,
                    forward=True,
                )
            bbox = figure_tight_bbox(fig_export)

        rasterized_artists = []
        if not skip_rasterize and _is_vector_output(output_filename):
            rasterized_artists = auto_rasterize_figure(
                fig_export,
                scatter_threshold=rasterize_scatter_threshold,
                image_pixel_threshold=rasterize_image_pixel_threshold,
                line_vertex_threshold=rasterize_line_vertex_threshold,
            )

        if verbose:
            print(f"tight bbox inches: {bbox.width:.2f} {bbox.height:.2f}")
            if rasterized_artists:
                print(f"auto-rasterized artists: {', '.join(rasterized_artists)}")

        fig_export.savefig(
            output_filename,
            dpi=dpi,
            bbox_inches="tight",
            pad_inches=0.0,
        )


def _is_vector_output(path: str | Path) -> bool:
    return Path(path).suffix.lower() in {".pdf", ".svg", ".eps", ".ps", ".pgf"}


__all__ = ["ResolvedStyle", "save_fig"]
