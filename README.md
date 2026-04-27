# pubify-tex

`pubify-tex` owns the LaTeX layer for pubify figure export. It provides the
`pubify.sty` asset, template writing, LaTeX layout geometry, and
document-aware `save_fig(...)` behavior by composing the Matplotlib-only
preparation API in `pubify-mpl`.

`pubify-tex` also owns the TeX publication figure typography profile. It passes
Latin Modern serif fallbacks, Computer Modern mathtext, `text.usetex=True`, and
the package LaTeX preamble explicitly into `pubify-mpl`.

## Install

```bash
pip install pubify-tex
```

## Documentation

- [Docs home](https://nvnunes.github.io/pubify-tex/)
- [Architecture](https://nvnunes.github.io/pubify-tex/architecture/)
- [Testing](https://nvnunes.github.io/pubify-tex/testing/)
- [API reference](https://nvnunes.github.io/pubify-tex/api/)

## Quick Start

```python
import matplotlib.pyplot as plt

from pubify_tex import prepare, save_fig

template = {
    "textwidth_in": 5.39643,
    "textheight_in": 7.58960,
}

fig, ax = plt.subplots()
ax.plot([0, 1], [0, 1])

prepare("tex", template=template)
save_fig(fig, "onewide", "tex/figures/demo.pdf", template=template)
```

Use `pubify-mpl` directly when you need TeX-free Matplotlib figure preparation.

## Public API

Package-root imports include:

- `DEFAULT_TEMPLATE`
- `install_pubify_package`
- `latex_layout_geometry`
- `normalized_template`
- `prepare`
- `pubify_rc_context`
- `ResolvedStyle`
- `save_fig`
- `use_template`
- `write_tex_template`
