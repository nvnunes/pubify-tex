"""LaTeX layout and export support for pubify Matplotlib figures."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from .export import ResolvedStyle, save_fig
from .layout import (
    DEFAULT_TEMPLATE,
    latex_layout_geometry,
    normalized_template,
    use_template,
)
from .layout import matplotlib_style_from_template as _matplotlib_style_from_template
from .resources import install_pubify_package, prepare, write_tex_template
from pubify_mpl import pubify_rc_context as _pubify_mpl_rc_context


@contextmanager
def pubify_rc_context(
    style: dict[str, Any] | None = None,
    *,
    extra_rcparams: dict[str, Any] | None = None,
) -> Iterator[None]:
    """Apply the Matplotlib construction rc context for a pubify TeX template."""

    with _pubify_mpl_rc_context(
        style=_matplotlib_style_from_template(style),
        extra_rcparams=extra_rcparams,
    ):
        yield

__all__ = [
    "DEFAULT_TEMPLATE",
    "install_pubify_package",
    "latex_layout_geometry",
    "normalized_template",
    "prepare",
    "pubify_rc_context",
    "ResolvedStyle",
    "save_fig",
    "use_template",
    "write_tex_template",
]
