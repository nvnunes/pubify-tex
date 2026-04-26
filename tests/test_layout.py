from pathlib import Path

import pytest

import pubify_tex
from pubify_tex.layout import latex_layout_geometry, matplotlib_style_from_template, normalized_template
from pubify_tex.resources import write_tex_template

def test_non_dict_template_raises():
    try:
        normalized_template("bogus")  # type: ignore[arg-type]
    except TypeError as exc:
        assert "template must be a template dictionary or None" in str(exc)
    else:
        raise AssertionError("Expected TypeError")


def test_partial_template_gets_policy_defaults():
    spec = normalized_template({"textwidth_in": 7.0, "textheight_in": 9.0})
    assert spec["textwidth_in"] == 7.0
    assert spec["base_fontsize_pt"] == 12.0
    assert spec["line_width_pt"] == -1.0
    assert spec["axes_line_width_pt"] == 0.8
    assert spec["tick_length_pt"] == 3.0
    assert spec["axes_labelsize_pt"] == 12.0
    assert spec["tick_labelsize_pt"] == 11.0
    assert spec["legend_fontsize_pt"] == 11.0
    assert spec["title_fontsize_pt"] == 13.0
    assert spec["caption_lineheight_pt"] == 13.6
    assert spec["subcaption_lineheight_pt"] == 13.6
    assert spec["caption_lineheight_in"] == 13.6 / 72.27
    assert spec["subcaption_lineheight_in"] == 13.6 / 72.27
    assert spec["col_gap_in"] == 7.0 * 0.02
    assert spec["caption_allowance_in"] == 0.08
    assert spec["subcaption_allowance_in"] == 0.08
    assert spec["subcaption_skip_in"] > 0
    assert spec["row_skip_in"] > 0
    assert spec["row_skip_in"] == 0.11
    assert spec["caption_skip_in"] == 0.11
    assert spec["post_caption_skip_in"] == 0.0


def test_package_root_exports_only_supported_public_helpers():
    assert "pubify_rc_context" in pubify_tex.__all__
    assert "matplotlib_style_from_template" not in pubify_tex.__all__


def test_normalized_template_rejects_unknown_options():
    with pytest.raises(ValueError, match="unknown template option"):
        normalized_template({"caption_skipn_in": 0.1})


@pytest.mark.parametrize("value", ["6.5", True])
def test_normalized_template_rejects_non_numeric_values(value):
    with pytest.raises(TypeError, match="must be a finite number"):
        normalized_template({"textwidth_in": value})


@pytest.mark.parametrize("value", [float("inf"), float("nan")])
def test_normalized_template_rejects_non_finite_values(value):
    with pytest.raises(ValueError, match="must be a finite number"):
        normalized_template({"textwidth_in": value})


@pytest.mark.parametrize("key", ["textwidth_in", "textheight_in", "caption_lineheight_pt"])
def test_normalized_template_rejects_non_positive_dimensions(key):
    with pytest.raises(ValueError, match="must be positive"):
        normalized_template({key: 0.0})


@pytest.mark.parametrize("key", ["row_skip_in", "caption_skip_in", "post_caption_skip_in"])
def test_normalized_template_rejects_negative_spacing(key):
    with pytest.raises(ValueError, match="must be non-negative"):
        normalized_template({key: -0.1})


def test_matplotlib_style_from_template_excludes_latex_layout_keys():
    style = matplotlib_style_from_template({"textwidth_in": 7.0, "textheight_in": 9.0})

    assert style == {
        "base_fontsize_pt": 12.0,
        "axes_labelsize_pt": 12.0,
        "tick_labelsize_pt": 11.0,
        "legend_fontsize_pt": 11.0,
        "title_fontsize_pt": 13.0,
        "line_width_pt": -1.0,
        "axes_line_width_pt": 0.8,
        "tick_length_pt": 3.0,
    }


def test_write_tex_template_matches_template(tmp_path):
    output = write_tex_template(tmp_path / "pubify-template.tex", {"textwidth_in": 7.0, "textheight_in": 9.0})
    text = output.read_text()
    assert "\\setlength{\\figcolgap}{0.14000in}" in text
    assert "\\setlength{\\figcaptionallowance}{0.08000in}" in text
    assert "\\providecommand{\\figbasefontsizept}{12.00000}" in text
    assert "\\setlength{\\figcaptionlineheight}{13.60000pt}" in text
    assert "\\setlength{\\figfullpageheight}{8.81000in}" in text
    assert "\\setlength{\\figstackheight}{8.81000in}" in text
    assert "\\setlength{\\figsubcaptionallowance}{0.08000in}" in text
    assert "\\setlength{\\figsubcaptionlineheight}{13.60000pt}" in text
    assert "\\setlength{\\figsubcaptionskip}{0.08000in}" in text
    assert "\\setlength{\\figcaptionskip}{0.11000in}" in text
    assert "\\setlength{\\figpostcaptionskip}{0.00000in}" in text
    assert "\\setlength{\\figrowgap}{0.11000in}" in text


def test_write_tex_template_accepts_directory(tmp_path):
    output = write_tex_template(tmp_path, {"textwidth_in": 7.0, "textheight_in": 9.0})
    assert output == tmp_path / "pubify-template.tex"
    assert output.exists()


def test_pubify_sty_fallback_defaults_match_python_defaults():
    spec = normalized_template()
    sty_path = Path("src/pubify_tex/assets/pubify.sty")
    text = sty_path.read_text()

    assert "\\setlength{\\figcaptionallowance}{0.08in}" in text
    assert "\\providecommand{\\figbasefontsizept}{12.0}" in text
    assert "\\setlength{\\figcaptionlineheight}{13.6pt}" in text
    assert "\\setlength{\\figsubcaptionallowance}{0.08in}" in text
    assert "\\setlength{\\figsubcaptionlineheight}{13.6pt}" in text
    assert "\\setlength{\\figsubcaptionskip}{0.08in}" in text
    assert "\\setlength{\\figrowgap}{0.11in}" in text
    assert "\\setlength{\\figcaptionskip}{0.11in}" in text
    assert "\\setlength{\\figpostcaptionskip}{0in}" in text
    assert spec["caption_allowance_in"] == 0.08
    assert spec["base_fontsize_pt"] == 12.0
    assert spec["line_width_pt"] == -1.0
    assert spec["axes_line_width_pt"] == 0.8
    assert spec["tick_length_pt"] == 3.0
    assert spec["axes_labelsize_pt"] == 12.0
    assert spec["tick_labelsize_pt"] == 11.0
    assert spec["legend_fontsize_pt"] == 11.0
    assert spec["title_fontsize_pt"] == 13.0
    assert spec["caption_lineheight_pt"] == 13.6
    assert spec["subcaption_allowance_in"] == 0.08
    assert spec["subcaption_lineheight_pt"] == 13.6
    assert spec["subcaption_skip_in"] == 0.08
    assert spec["row_skip_in"] == 0.11
    assert spec["caption_skip_in"] == 0.11
    assert spec["post_caption_skip_in"] == 0.0


def test_layout_geometry_samples():
    for layout in ["one", "twowide", "threewide", "two", "four", "nine"]:
        geom = latex_layout_geometry(layout)
        assert geom["width_in"] > 0
        assert geom["height_in"] > 0


def test_subcaption_skip_and_caption_skip_affect_wide_layout_height_geometry():
    base = {
        "textwidth_in": 6.5,
        "textheight_in": 8.5,
        "caption_skip_in": 0.2,
        "subcaption_skip_in": 0.1,
        "subcaption_allowance_in": 0.3,
    }
    geom_plain = latex_layout_geometry("twowide", layout_spec=base, caption_lines=1)
    geom_subcaption = latex_layout_geometry(
        "twowide",
        layout_spec=base,
        caption_lines=1,
        subcaption_lines=1,
    )
    assert geom_subcaption["height_in"] < geom_plain["height_in"]


def test_subcaption_skip_and_caption_skip_affect_stacked_height():
    base = {
        "textwidth_in": 6.5,
        "textheight_in": 8.5,
        "row_skip_in": 0.2,
        "caption_skip_in": 0.15,
        "subcaption_skip_in": 0.1,
        "subcaption_allowance_in": 0.25,
    }
    geom_plain = latex_layout_geometry("four", layout_spec=base, caption_lines=1)
    geom_subcaption = latex_layout_geometry(
        "four",
        layout_spec=base,
        caption_lines=1,
        subcaption_lines=1,
    )
    assert geom_subcaption["height_in"] < geom_plain["height_in"]
