from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.transforms import Bbox
import pytest

from pubify_tex import save_fig, use_template, write_tex_template
from pubify_tex.layout import normalized_template
import pubify_tex.export as export_mod
from pubify_tex.export import ResolvedStyle
from pubify_mpl import auto_rasterize_figure, figure_tight_bbox
from pubify_mpl.adjust import (
    force_font_family,
    hide_labels as public_hide_labels,
    remove_outside_padding,
    set_axes_labelsize,
    set_legend_fontsize,
    set_line_width,
    set_spine_width,
    set_tick_labelsize,
    set_tick_length,
    set_tick_width,
    set_title_fontsize,
)
from pubify_mpl.export import clone_figure_pickle

ARTICLE_TEMPLATE = {
    "textwidth_in": 5.39643,
    "textheight_in": 7.58960,
}

AO4ELT_TEMPLATE = {
    "textwidth_in": 6.75,
    "textheight_in": 9.70,
}


def make_composite_figure(*, with_shared_colorbar: bool = True):
    fig, axs = plt.subplots(1, 2, figsize=(6, 3))
    images = []
    for idx, ax in enumerate(axs):
        image = ax.imshow(
            [[idx + 1, idx + 2], [idx + 3, idx + 4]],
            origin="lower",
        )
        images.append(image)
        ax.set_xlabel(f"X {idx}")
        ax.set_ylabel(f"Y {idx}")
        ax.set_title(f"Panel {idx}")
        ax.text(0.5, 0.5, f"Note {idx}", transform=ax.transAxes)
        ax.grid(True)

    if with_shared_colorbar:
        cbar = fig.colorbar(images[-1], ax=axs, shrink=0.85)
        cbar.set_label("Scale")
        fig.subplots_adjust(wspace=0.3, right=0.88, top=0.82)
    else:
        fig.subplots_adjust(wspace=0.3, top=0.82)

    fig.suptitle("Composite Figure")
    fig.supxlabel("Shared X")
    fig.supylabel("Shared Y")
    return fig, axs


def content_bbox_in_figure_coords(fig: Figure) -> Bbox:
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    boxes = [ax.get_position().frozen() for ax in fig.axes if ax.get_visible()]
    for text in (getattr(fig, "_suptitle", None), getattr(fig, "_supxlabel", None), getattr(fig, "_supylabel", None)):
        if text is not None and text.get_visible():
            boxes.append(fig.transFigure.inverted().transform_bbox(text.get_window_extent(renderer)).frozen())
    return Bbox.from_extents(
        min(box.x0 for box in boxes),
        min(box.y0 for box in boxes),
        max(box.x1 for box in boxes),
        max(box.y1 for box in boxes),
    )
def test_save_basic_line_plot(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([0, 1, 2], [0, 1, 0])
    output = save_fig(
        fig,
        "onewide",
        tmp_path / "line-demo.pdf",
        template=ARTICLE_TEMPLATE,
        skip_rasterize=True,
    )
    assert output is None
    assert (tmp_path / "line-demo.pdf").exists()
    plt.close(fig)


def test_save_accepts_force_width_with_layout(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    output = save_fig(
        fig,
        "one",
        tmp_path / "force-width-demo.pdf",
        template=ARTICLE_TEMPLATE,
        caption_lines=0,
        force_width=2.3,
        skip_rasterize=True,
    )
    assert output is None
    assert (tmp_path / "force-width-demo.pdf").exists()
    plt.close(fig)


def test_save_wide_layout_uses_full_width_without_height_cap(tmp_path, monkeypatch):
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.plot([0, 1], [0, 1])
    captured = {}

    original_layout_geometry = export_mod.latex_layout_geometry
    original_savefig = Figure.savefig

    def fake_layout_geometry(layout, layout_spec, caption_lines, subcaption_lines):
        geometry = original_layout_geometry(
            layout,
            layout_spec,
            caption_lines=caption_lines,
            subcaption_lines=subcaption_lines,
        )
        geometry["width_in"] = 4.5
        geometry["height_in"] = 1.0
        return geometry

    def fake_savefig(self, *args, **kwargs):
        bbox = figure_tight_bbox(self)
        captured["width"] = bbox.width
        captured["height"] = bbox.height

    monkeypatch.setattr(export_mod, "latex_layout_geometry", fake_layout_geometry)
    monkeypatch.setattr(Figure, "savefig", fake_savefig)

    output = save_fig(
        fig,
        "twowide",
        tmp_path / "force-width-full-demo.pdf",
        template=ARTICLE_TEMPLATE,
        skip_rasterize=True,
    )

    assert output is None
    assert captured["width"] == pytest.approx(4.5, abs=0.05)
    assert captured["height"] > 1.0
    plt.close(fig)


def test_save_figure_preserves_subplots_and_shared_colorbar(tmp_path):
    fig, axs = make_composite_figure()
    observed = {}

    def prepare_export(fig_copy):
        observed["same_object"] = fig_copy is fig
        observed["axes_count"] = len(fig_copy.axes)
        observed["titles"] = [ax.get_title() for ax in fig_copy.axes if ax.get_title()]
        observed["suptitle"] = fig_copy._suptitle.get_text() if fig_copy._suptitle else None
        observed["supxlabel"] = fig_copy._supxlabel.get_text() if fig_copy._supxlabel else None
        observed["supylabel"] = fig_copy._supylabel.get_text() if fig_copy._supylabel else None
        observed["has_scale_label"] = any(ax.get_ylabel() == "Scale" for ax in fig_copy.axes)

    save_fig(
        fig,
        "onewide",
        tmp_path / "composite-shared-cbar.pdf",
        template=ARTICLE_TEMPLATE,
        keep_titles=True,
        prepare_export=prepare_export,
        skip_rasterize=True,
    )

    assert observed["same_object"] is False
    assert observed["axes_count"] == 3
    assert observed["titles"] == ["Panel 0", "Panel 1"]
    assert observed["suptitle"] == "Composite Figure"
    assert observed["supxlabel"] == "Shared X"
    assert observed["supylabel"] == "Shared Y"
    assert observed["has_scale_label"] is True
    assert (tmp_path / "composite-shared-cbar.pdf").exists()
    plt.close(fig)


def test_save_axes_still_isolates_single_panel_from_composite_figure(tmp_path):
    fig, axs = make_composite_figure()
    observed = {}

    def prepare_export(fig_copy):
        observed["axes_count"] = len(fig_copy.axes)
        observed["titles"] = [ax.get_title() for ax in fig_copy.axes if ax.get_title()]
        observed["has_scale_label"] = any(ax.get_ylabel() == "Scale" for ax in fig_copy.axes)

    save_fig(
        axs[1],
        "onewide",
        tmp_path / "isolated-panel.pdf",
        template=ARTICLE_TEMPLATE,
        keep_titles=True,
        prepare_export=prepare_export,
        skip_rasterize=True,
    )

    assert observed["axes_count"] == 2
    assert observed["titles"] == ["Panel 1"]
    assert observed["has_scale_label"] is True
    assert (tmp_path / "isolated-panel.pdf").exists()
    plt.close(fig)


def test_save_can_skip_clone_step(tmp_path, monkeypatch):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    called = False

    def fail_clone(_fig):
        nonlocal called
        called = True
        raise AssertionError("clone should not run when skip_clone=True")

    monkeypatch.setattr("pubify_mpl.export.clone_figure_pickle", fail_clone)

    output = save_fig(
        fig,
        "onewide",
        tmp_path / "skip-clone-demo.pdf",
        template=ARTICLE_TEMPLATE,
        skip_clone=True,
        skip_rasterize=True,
    )

    assert output is None
    assert called is False
    assert (tmp_path / "skip-clone-demo.pdf").exists()
    plt.close(fig)


def test_save_force_width_rejects_too_wide_request(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    try:
        save_fig(
            fig,
            "one",
            tmp_path / "too-wide.pdf",
            template=ARTICLE_TEMPLATE,
            force_width=10.0,
            skip_rasterize=True,
        )
    except ValueError as exc:
        assert "exceeds the available width" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
    plt.close(fig)


def test_save_force_width_rejects_wide_layout(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    with pytest.raises(ValueError, match="not supported for layouts"):
        save_fig(
            fig,
            "twowide",
            tmp_path / "wide-force-width-invalid.pdf",
            template=ARTICLE_TEMPLATE,
            force_width=2.0,
            skip_rasterize=True,
        )
    plt.close(fig)


def test_save_force_width_rejects_string_value(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    with pytest.raises(ValueError, match="must be a float in inches"):
        save_fig(
            fig,
            "onewide",
            tmp_path / "string-force-width.pdf",
            template=ARTICLE_TEMPLATE,
            force_width="wide",
            skip_rasterize=True,
        )
    plt.close(fig)


def test_save_rejects_force_width_and_force_height_together(tmp_path):
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.plot([0, 1], [0, 1])
    with pytest.raises(ValueError, match="mutually exclusive"):
        save_fig(
            fig,
            "one",
            tmp_path / "width-and-height.pdf",
            template=ARTICLE_TEMPLATE,
            force_width=2.0,
            force_height=2.0,
            skip_rasterize=True,
        )
    plt.close(fig)


def test_save_force_height_caps_wide_layout(tmp_path, monkeypatch):
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.plot([0, 1], [0, 1])
    captured = {}
    original_layout_geometry = export_mod.latex_layout_geometry

    def fake_layout_geometry(layout, layout_spec, caption_lines, subcaption_lines):
        geometry = original_layout_geometry(
            layout,
            layout_spec,
            caption_lines=caption_lines,
            subcaption_lines=subcaption_lines,
        )
        geometry["width_in"] = 4.5
        geometry["height_in"] = 1.0
        return geometry

    def fake_savefig(self, *args, **kwargs):
        bbox = figure_tight_bbox(self)
        captured["width"] = bbox.width
        captured["height"] = bbox.height

    monkeypatch.setattr(export_mod, "latex_layout_geometry", fake_layout_geometry)
    monkeypatch.setattr(Figure, "savefig", fake_savefig)

    output = save_fig(
        fig,
        "onewide",
        tmp_path / "force-height-wide.pdf",
        template=ARTICLE_TEMPLATE,
        force_height=2.0,
        skip_rasterize=True,
    )

    assert output is None
    assert captured["height"] <= 2.0 + 0.05
    assert captured["width"] < 4.5
    plt.close(fig)


def test_save_force_height_caps_nonwide_layout(tmp_path, monkeypatch):
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.plot([0, 1], [0, 1])
    captured = {}

    def fake_savefig(self, *args, **kwargs):
        bbox = figure_tight_bbox(self)
        captured["height"] = bbox.height

    monkeypatch.setattr(Figure, "savefig", fake_savefig)

    output = save_fig(
        fig,
        "one",
        tmp_path / "force-height-one.pdf",
        template=ARTICLE_TEMPLATE,
        force_height=2.0,
        skip_rasterize=True,
    )

    assert output is None
    assert captured["height"] <= 2.0 + 0.05
    plt.close(fig)


def test_save_accepts_cwd_relative_filename(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    output = save_fig(fig, "onewide", "cwd-demo", template=ARTICLE_TEMPLATE, skip_rasterize=True)
    assert output is None
    assert Path("cwd-demo.pdf").exists()
    plt.close(fig)


def test_save_creates_relative_parent_directories(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    output = save_fig(
        fig,
        "onewide",
        "tex/figures/plot.pdf",
        template=ARTICLE_TEMPLATE,
        skip_rasterize=True,
    )
    assert output is None
    assert Path("tex/figures/plot.pdf").exists()
    plt.close(fig)


def test_save_absolute_missing_parent_raises_nicer_error(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    missing_output = tmp_path / "missing" / "plot.pdf"
    try:
        save_fig(fig, "onewide", missing_output, template=ARTICLE_TEMPLATE, skip_rasterize=True)
    except FileNotFoundError as exc:
        assert "Parent directory does not exist" in str(exc)
        assert str(missing_output) in str(exc)
    else:
        raise AssertionError("Expected FileNotFoundError")
    plt.close(fig)


def test_save_uses_context_default_template(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    template = {"textwidth_in": 6.5, "textheight_in": 8.5}
    with use_template(template):
        output = save_fig(fig, "onewide", tmp_path / "context-demo.pdf", skip_rasterize=True)
    assert output is None
    assert (tmp_path / "context-demo.pdf").exists()
    plt.close(fig)


def test_save_template_argument_overrides_context_default(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    with use_template({"textwidth_in": 6.5, "textheight_in": 8.5}):
        output = save_fig(
            fig,
            "onewide",
            tmp_path / "override-demo.pdf",
            template=AO4ELT_TEMPLATE,
            skip_rasterize=True,
        )
    assert output is None
    assert (tmp_path / "override-demo.pdf").exists()
    plt.close(fig)


def test_save_rejects_non_string_layout(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    try:
        save_fig(fig, 3.25, tmp_path / "bad-layout.pdf", template=ARTICLE_TEMPLATE, skip_rasterize=True)
    except TypeError as exc:
        assert "layout must be a named layout string" in str(exc)
    else:
        raise AssertionError("Expected TypeError")
    plt.close(fig)


def test_write_tex_template_explicitly(tmp_path):
    tex_template = write_tex_template(tmp_path / "pubify-template.tex", template=ARTICLE_TEMPLATE)
    assert tex_template.exists()


def test_auto_rasterize_scatter_heavy_plot():
    fig, ax = plt.subplots()
    xs = list(range(1500))
    ys = [x % 17 for x in xs]
    coll = ax.scatter(xs, ys, s=2)
    rasterized = auto_rasterize_figure(fig)
    assert coll.get_rasterized() is True
    assert rasterized
    plt.close(fig)


def test_auto_rasterize_uses_custom_thresholds():
    fig, ax = plt.subplots()
    xs = list(range(20))
    ys = [x % 5 for x in xs]
    coll = ax.scatter(xs, ys, s=2)
    rasterized = auto_rasterize_figure(fig, scatter_threshold=10)
    assert coll.get_rasterized() is True
    assert rasterized
    plt.close(fig)


def test_save_passes_rasterize_thresholds_to_helper(tmp_path, monkeypatch):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    captured = {}

    def fake_auto_rasterize_figure(
        fig_copy,
        *,
        scatter_threshold,
        image_pixel_threshold,
        line_vertex_threshold,
    ):
        captured["fig_copy"] = fig_copy
        captured["scatter_threshold"] = scatter_threshold
        captured["image_pixel_threshold"] = image_pixel_threshold
        captured["line_vertex_threshold"] = line_vertex_threshold
        return []

    monkeypatch.setattr("pubify_tex.export.auto_rasterize_figure", fake_auto_rasterize_figure)

    save_fig(
        fig,
        "onewide",
        tmp_path / "thresholds-demo.pdf",
        template=ARTICLE_TEMPLATE,
        rasterize_scatter_threshold=11,
        rasterize_image_pixel_threshold=22,
        rasterize_line_vertex_threshold=33,
    )

    assert captured["scatter_threshold"] == 11
    assert captured["image_pixel_threshold"] == 22
    assert captured["line_vertex_threshold"] == 33
    assert captured["fig_copy"] is not fig
    plt.close(fig)


def test_prepare_export_hook_mutates_only_export_copy(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    original_linewidth = ax.lines[0].get_linewidth()
    observed = {}

    def prepare_export(fig_copy):
        observed["called"] = True
        observed["same_object"] = fig_copy is fig
        fig_copy.axes[0].lines[0].set_linewidth(7.0)

    output = save_fig(
        fig,
        "onewide",
        tmp_path / "edit-copy-demo.pdf",
        template=ARTICLE_TEMPLATE,
        prepare_export=prepare_export,
        skip_rasterize=True,
    )

    assert output is None
    assert observed["called"] is True
    assert observed["same_object"] is False
    assert fig.axes[0].lines[0].get_linewidth() == original_linewidth
    assert (tmp_path / "edit-copy-demo.pdf").exists()
    plt.close(fig)


def test_prepare_export_can_receive_resolved_style(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1], label="demo")
    ax.legend()
    ax.set_xlabel("X")
    ax.set_title("Title")
    observed = {}

    def prepare_export(fig_copy, style):
        copied_ax = fig_copy.axes[0]
        observed["same_object"] = fig_copy is fig
        observed["style"] = style
        observed["xlabel_size"] = copied_ax.xaxis.label.get_fontsize()
        observed["tick_size"] = copied_ax.get_xticklabels()[0].get_fontsize()
        observed["legend_size"] = copied_ax.get_legend().get_texts()[0].get_fontsize()
        observed["title_size"] = copied_ax.title.get_fontsize()

    save_fig(
        fig,
        "onewide",
        tmp_path / "prepare-copy-style.pdf",
        template={
            **ARTICLE_TEMPLATE,
            "base_fontsize_pt": 11.0,
            "axes_labelsize_pt": 14.0,
            "tick_labelsize_pt": 12.5,
            "legend_fontsize_pt": 10.5,
            "title_fontsize_pt": 15.0,
            "line_width_pt": 2.5,
            "axes_line_width_pt": 1.1,
            "tick_length_pt": 4.5,
        },
        keep_titles=True,
        prepare_export=prepare_export,
        skip_rasterize=True,
    )

    assert observed["same_object"] is False
    assert isinstance(observed["style"], ResolvedStyle)
    assert observed["style"] == ResolvedStyle(
        font_family="serif",
        base_fontsize_pt=11.0,
        axes_labelsize_pt=14.0,
        tick_labelsize_pt=12.5,
        legend_fontsize_pt=10.5,
        title_fontsize_pt=15.0,
        line_width_pt=2.5,
        axes_line_width_pt=1.1,
        tick_length_pt=4.5,
    )
    assert observed["xlabel_size"] == observed["style"].axes_labelsize_pt
    assert observed["tick_size"] == observed["style"].tick_labelsize_pt
    assert observed["legend_size"] == observed["style"].legend_fontsize_pt
    assert observed["title_size"] == observed["style"].title_fontsize_pt
    plt.close(fig)


def test_save_figure_cleanup_flags_apply_across_all_axes(tmp_path):
    fig, axs = make_composite_figure(with_shared_colorbar=False)
    observed = {}

    def prepare_export(fig_copy):
        observed["xlabels"] = [ax.get_xlabel() for ax in fig_copy.axes]
        observed["ylabels"] = [ax.get_ylabel() for ax in fig_copy.axes]
        observed["supxlabel"] = fig_copy._supxlabel.get_text() if fig_copy._supxlabel else None
        observed["supylabel"] = fig_copy._supylabel.get_text() if fig_copy._supylabel else None
        observed["texts"] = [len(ax.texts) for ax in fig_copy.axes]
        observed["xticks"] = [list(ax.get_xticks()) for ax in fig_copy.axes]
        observed["yticks"] = [list(ax.get_yticks()) for ax in fig_copy.axes]
        observed["grid_visible"] = [
            any(line.get_visible() for line in ax.get_xgridlines() + ax.get_ygridlines())
            for ax in fig_copy.axes
        ]

    save_fig(
        fig,
        "onewide",
        tmp_path / "composite-cleanup.pdf",
        template=ARTICLE_TEMPLATE,
        hide_labels=True,
        hide_annotations=True,
        hide_ticks=True,
        hide_grid=True,
        keep_titles=True,
        prepare_export=prepare_export,
        skip_rasterize=True,
    )

    assert observed["xlabels"] == ["", ""]
    assert observed["ylabels"] == ["", ""]
    assert observed["supxlabel"] == ""
    assert observed["supylabel"] == ""
    assert observed["texts"] == [0, 0]
    assert observed["xticks"] == [[], []]
    assert observed["yticks"] == [[], []]
    assert observed["grid_visible"] == [False, False]
    plt.close(fig)


def test_save_figure_hide_cbar_removes_all_colorbars(tmp_path):
    fig, axs = make_composite_figure()
    observed = {}

    def prepare_export(fig_copy):
        observed["axes_count"] = len(fig_copy.axes)
        observed["has_scale_label"] = any(ax.get_ylabel() == "Scale" for ax in fig_copy.axes)

    save_fig(
        fig,
        "onewide",
        tmp_path / "composite-hide-cbar.pdf",
        template=ARTICLE_TEMPLATE,
        hide_cbar=True,
        keep_titles=True,
        prepare_export=prepare_export,
        skip_rasterize=True,
    )

    assert observed["axes_count"] == 2
    assert observed["has_scale_label"] is False
    plt.close(fig)


def test_save_figure_keep_titles_false_clears_axes_titles_and_suptitle(tmp_path):
    fig, axs = make_composite_figure(with_shared_colorbar=False)
    observed = {}

    def prepare_export(fig_copy):
        observed["titles"] = [ax.get_title() for ax in fig_copy.axes]
        observed["suptitle"] = fig_copy._suptitle.get_text() if fig_copy._suptitle else None

    save_fig(
        fig,
        "onewide",
        tmp_path / "composite-clear-titles.pdf",
        template=ARTICLE_TEMPLATE,
        prepare_export=prepare_export,
        skip_rasterize=True,
    )

    assert observed["titles"] == ["", ""]
    assert observed["suptitle"] == ""
    plt.close(fig)


def test_save_figure_keep_titles_true_preserves_axes_titles_and_suptitle(tmp_path):
    fig, axs = make_composite_figure(with_shared_colorbar=False)
    observed = {}

    def prepare_export(fig_copy):
        observed["titles"] = [ax.get_title() for ax in fig_copy.axes]
        observed["suptitle"] = fig_copy._suptitle.get_text() if fig_copy._suptitle else None

    save_fig(
        fig,
        "onewide",
        tmp_path / "composite-keep-titles.pdf",
        template=ARTICLE_TEMPLATE,
        keep_titles=True,
        prepare_export=prepare_export,
        skip_rasterize=True,
    )

    assert observed["titles"] == ["Panel 0", "Panel 1"]
    assert observed["suptitle"] == "Composite Figure"
    plt.close(fig)


def test_save_figure_uses_uniform_scaling_for_default_composite_aspect(tmp_path, monkeypatch):
    fig, axs = plt.subplots(2, 1, figsize=(3, 6))
    for idx, ax in enumerate(axs):
        ax.plot([0, 1], [idx, idx + 1])
        ax.set_title(f"Panel {idx}")
    fig.suptitle("Tall Composite")

    recorded_scales = []

    def fake_layout_geometry(*args, **kwargs):
        return {
            "layout": "onewide",
            "cols": 1,
            "rows": 1,
            "width_in": 4.0,
            "height_in": 1.0,
            "height_mode": "single_row",
            "has_subcaption": False,
            "layout_spec": normalized_template(ARTICLE_TEMPLATE),
        }

    original_set_size_inches = Figure.set_size_inches

    def record_set_size_inches(self, w, h=None, *args, **kwargs):
        current_w, current_h = self.get_size_inches()
        if h is None:
            new_w, new_h = w
        else:
            new_w, new_h = w, h
        recorded_scales.append((new_w / current_w, new_h / current_h))
        return original_set_size_inches(self, w, h, *args, **kwargs)

    monkeypatch.setattr(export_mod, "latex_layout_geometry", fake_layout_geometry)
    monkeypatch.setattr(Figure, "set_size_inches", record_set_size_inches)

    save_fig(
        fig,
        "onewide",
        tmp_path / "composite-aspect.pdf",
        template=ARTICLE_TEMPLATE,
        keep_titles=True,
        skip_rasterize=True,
    )

    assert recorded_scales
    assert all(x_scale == pytest.approx(y_scale, rel=1e-6) for x_scale, y_scale in recorded_scales)
    plt.close(fig)


def test_remove_outside_padding_improves_composite_figure_outer_margins():
    fig, axs = make_composite_figure(with_shared_colorbar=False)
    fig.subplots_adjust(left=0.20, right=0.78, bottom=0.22, top=0.78, wspace=0.35)
    content_before = content_bbox_in_figure_coords(fig)

    remove_outside_padding(fig)

    content_after = content_bbox_in_figure_coords(fig)

    assert content_after.x0 < content_before.x0
    assert content_after.x1 > content_before.x1
    assert content_after.y0 < content_before.y0
    assert content_after.y1 > content_before.y1
    plt.close(fig)


def test_hide_annotations_removes_axis_text(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    ax.text(0.5, 0.5, "demo", transform=ax.transAxes)
    output = save_fig(fig, "onewide", tmp_path / "annot-demo.pdf", template=ARTICLE_TEMPLATE, hide_annotations=True, skip_rasterize=True)
    assert output is None
    assert (tmp_path / "annot-demo.pdf").exists()
    plt.close(fig)


def test_save_routes_hide_labels_through_adjust_helper(tmp_path, monkeypatch):
    fig, ax = plt.subplots()
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    calls = []

    def fake_hide_labels(fig_copy):
        calls.append(fig_copy)
        public_hide_labels(fig_copy)

    monkeypatch.setattr("pubify_mpl.export.adjust.hide_labels", fake_hide_labels)

    save_fig(
        fig,
        "onewide",
        tmp_path / "hide-labels-demo.pdf",
        template=ARTICLE_TEMPLATE,
        hide_labels=True,
        skip_rasterize=True,
    )

    assert len(calls) == 1
    assert calls[0] is not fig
    plt.close(fig)


def test_prepare_export_runs_after_standard_cleanup(tmp_path):
    fig, ax = plt.subplots()
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    observed = {}

    def prepare_export(fig_copy):
        observed["xlabel"] = fig_copy.axes[0].get_xlabel()
        observed["ylabel"] = fig_copy.axes[0].get_ylabel()

    save_fig(
        fig,
        "onewide",
        tmp_path / "prepare-copy-cleanup-order.pdf",
        template=ARTICLE_TEMPLATE,
        hide_labels=True,
        prepare_export=prepare_export,
        skip_rasterize=True,
    )

    assert observed["xlabel"] == ""
    assert observed["ylabel"] == ""
    plt.close(fig)


def test_prepare_export_rejects_incompatible_callback_signature(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])

    def prepare_export(fig_copy, style, extra):
        raise AssertionError("should not be called")

    with pytest.raises(TypeError, match="prepare_export must accept either one positional argument"):
        save_fig(
            fig,
            "onewide",
            tmp_path / "bad-prepare-copy-signature.pdf",
            template=ARTICLE_TEMPLATE,
            prepare_export=prepare_export,
            skip_rasterize=True,
        )

    plt.close(fig)


def test_save_uses_template_styling_defaults_before_prepare_export(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1], label="demo")
    ax.legend()
    observed = {}

    def prepare_export(fig_copy):
        copied_ax = fig_copy.axes[0]
        observed["line_width"] = copied_ax.lines[0].get_linewidth()
        observed["spine_width"] = copied_ax.spines["bottom"].get_linewidth()
        observed["tick_width"] = copied_ax.xaxis.majorTicks[0].tick1line.get_markeredgewidth()
        observed["tick_length"] = copied_ax.xaxis.majorTicks[0].tick1line.get_markersize()

    save_fig(
        fig,
        "onewide",
        tmp_path / "template-style-defaults.pdf",
        template={
            **ARTICLE_TEMPLATE,
            "line_width_pt": 2.5,
            "axes_line_width_pt": 1.1,
            "tick_length_pt": 4.5,
        },
        prepare_export=prepare_export,
        skip_rasterize=True,
    )

    assert observed["line_width"] == 2.5
    assert observed["spine_width"] == 1.1
    assert observed["tick_width"] == 1.1
    assert observed["tick_length"] == 4.5
    plt.close(fig)


def test_save_uses_template_text_style_defaults_before_prepare_export(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1], label="demo")
    ax.legend()
    fig.supxlabel("Shared X")
    fig.supylabel("Shared Y")
    observed = {}

    def prepare_export(fig_copy):
        copied_ax = fig_copy.axes[0]
        observed["xlabel_size"] = copied_ax.xaxis.label.get_fontsize()
        observed["supxlabel_size"] = fig_copy._supxlabel.get_fontsize() if fig_copy._supxlabel else None
        observed["supylabel_size"] = fig_copy._supylabel.get_fontsize() if fig_copy._supylabel else None
        observed["tick_size"] = copied_ax.get_xticklabels()[0].get_fontsize()
        observed["legend_size"] = copied_ax.get_legend().get_texts()[0].get_fontsize()
        observed["title_size"] = copied_ax.title.get_fontsize()

    ax.set_xlabel("X")
    ax.set_title("Title")
    save_fig(
        fig,
        "onewide",
        tmp_path / "template-text-style-defaults.pdf",
        template={
            **ARTICLE_TEMPLATE,
            "axes_labelsize_pt": 14.0,
            "tick_labelsize_pt": 12.5,
            "legend_fontsize_pt": 10.5,
            "title_fontsize_pt": 15.0,
        },
        keep_titles=True,
        prepare_export=prepare_export,
        skip_rasterize=True,
    )

    assert observed["xlabel_size"] == 14.0
    assert observed["supxlabel_size"] == 14.0
    assert observed["supylabel_size"] == 14.0
    assert observed["tick_size"] == 12.5
    assert observed["legend_size"] == 10.5
    assert observed["title_size"] == 15.0
    plt.close(fig)


def test_save_skips_template_style_override_when_value_is_negative(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    ax.lines[0].set_linewidth(2.7)
    for spine in ax.spines.values():
        spine.set_linewidth(1.7)
    ax.tick_params(width=1.7, length=6.0)
    observed = {}

    def prepare_export(fig_copy):
        copied_ax = fig_copy.axes[0]
        observed["line_width"] = copied_ax.lines[0].get_linewidth()
        observed["spine_width"] = copied_ax.spines["bottom"].get_linewidth()
        observed["tick_width"] = copied_ax.xaxis.majorTicks[0].tick1line.get_markeredgewidth()
        observed["tick_length"] = copied_ax.xaxis.majorTicks[0].tick1line.get_markersize()

    save_fig(
        fig,
        "onewide",
        tmp_path / "template-style-skip.pdf",
        template={
            **ARTICLE_TEMPLATE,
            "line_width_pt": -1,
            "axes_line_width_pt": -1,
            "tick_length_pt": -1,
        },
        prepare_export=prepare_export,
        skip_rasterize=True,
    )

    assert observed["line_width"] == 2.7
    assert observed["spine_width"] == 1.7
    assert observed["tick_width"] == 1.7
    assert observed["tick_length"] == 6.0
    plt.close(fig)


def test_save_skips_template_text_style_override_when_value_is_negative(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1], label="demo")
    ax.set_xlabel("X")
    ax.set_title("Title")
    ax.legend()
    ax.xaxis.label.set_fontsize(17.0)
    ax.title.set_fontsize(18.0)
    ax.tick_params(labelsize=14.0)
    for text in ax.get_legend().get_texts():
        text.set_fontsize(13.0)
    observed = {}

    def prepare_export(fig_copy):
        copied_ax = fig_copy.axes[0]
        observed["xlabel_size"] = copied_ax.xaxis.label.get_fontsize()
        observed["tick_size"] = copied_ax.get_xticklabels()[0].get_fontsize()
        observed["legend_size"] = copied_ax.get_legend().get_texts()[0].get_fontsize()
        observed["title_size"] = copied_ax.title.get_fontsize()

    save_fig(
        fig,
        "onewide",
        tmp_path / "template-text-style-skip.pdf",
        template={
            **ARTICLE_TEMPLATE,
            "axes_labelsize_pt": -1,
            "tick_labelsize_pt": -1,
            "legend_fontsize_pt": -1,
            "title_fontsize_pt": -1,
        },
        keep_titles=True,
        prepare_export=prepare_export,
        skip_rasterize=True,
    )

    assert observed["xlabel_size"] == 17.0
    assert observed["tick_size"] == 14.0
    assert observed["legend_size"] == 13.0
    assert observed["title_size"] == 18.0
    plt.close(fig)


def test_save_hide_cbar_removes_single_panel_colorbar(tmp_path):
    fig, ax = plt.subplots()
    img = ax.imshow([[1, 2], [3, 4]])
    fig.colorbar(img, ax=ax)

    save_fig(
        fig,
        "onewide",
        tmp_path / "hide-cbar-demo.pdf",
        template=ARTICLE_TEMPLATE,
        hide_cbar=True,
        skip_rasterize=True,
    )

    assert (tmp_path / "hide-cbar-demo.pdf").exists()
    plt.close(fig)


def test_force_font_family_updates_axis_text_annotations():
    fig, ax = plt.subplots()
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.plot([0, 1], [0, 1], label="demo")
    ax.legend()
    annotation = ax.text(0.5, 0.5, "demo", transform=ax.transAxes)
    fig2 = clone_figure_pickle(fig)

    force_font_family(fig2)

    copied_ax = fig2.axes[0]
    assert copied_ax.texts[0].get_fontfamily() == ["serif"]
    assert copied_ax.xaxis.label.get_fontfamily() == ["serif"]
    assert copied_ax.yaxis.label.get_fontfamily() == ["serif"]
    assert all(tick.get_fontfamily() == ["serif"] for tick in copied_ax.get_xticklabels())
    assert all(text.get_fontfamily() == ["serif"] for text in copied_ax.get_legend().get_texts())

    plt.close(fig)
    plt.close(fig2)


def test_force_font_family_updates_figure_text():
    fig, ax = plt.subplots()
    fig.text(0.5, 0.5, "figure note")
    fig.supxlabel("Shared X")
    fig.supylabel("Shared Y")
    fig2 = clone_figure_pickle(fig)

    force_font_family(fig2)

    assert fig2.texts[0].get_fontfamily() == ["serif"]
    assert fig2._supxlabel.get_fontfamily() == ["serif"]
    assert fig2._supylabel.get_fontfamily() == ["serif"]

    plt.close(fig)
    plt.close(fig2)


def test_inset_axes_receive_publication_font_and_style():
    fig, ax = plt.subplots()
    ax.set_xticks([0.0, 0.5, 1.0])
    ax.set_yticks([0.0, 0.5, 1.0])
    inset = ax.inset_axes([0.6, 0.1, 0.35, 0.35])
    inset.set_xticks([0.0, 0.5, 1.0])
    inset.set_yticks([0.0, 0.5, 1.0])
    fig2 = clone_figure_pickle(fig)

    force_font_family(fig2)
    set_axes_labelsize(fig2, 12.0)
    set_tick_labelsize(fig2, 11.0)
    set_legend_fontsize(fig2, 11.0)
    set_title_fontsize(fig2, 13.0)
    set_line_width(fig2, 1.2)
    set_spine_width(fig2, 0.8)
    set_tick_width(fig2, 0.8)
    set_tick_length(fig2, 3.0)

    copied_main = fig2.axes[0]
    copied_inset = copied_main.child_axes[0]
    assert all(tick.get_fontfamily() == ["serif"] for tick in copied_inset.get_xticklabels())
    assert all(tick.get_fontfamily() == ["serif"] for tick in copied_inset.get_yticklabels())
    assert copied_inset.get_xticklabels()[0].get_fontsize() == copied_main.get_xticklabels()[0].get_fontsize()
    assert copied_inset.get_yticklabels()[0].get_fontsize() == copied_main.get_yticklabels()[0].get_fontsize()
    assert copied_inset.spines["bottom"].get_linewidth() == copied_main.spines["bottom"].get_linewidth()

    plt.close(fig)
    plt.close(fig2)
