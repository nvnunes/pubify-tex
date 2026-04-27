# Architecture

`pubify-tex` owns the LaTeX-specific layer of the pubify figure workflow.

## Package Role

Package-owned behavior:

- `pubify.sty` runtime asset installation
- `pubify-template.tex` writing
- LaTeX template normalization and layout geometry
- LaTeX-aware `save_fig(...)` using named figure layouts
- TeX publication figure typography: Latin Modern serif fallbacks, Computer
  Modern mathtext, `text.usetex=True`, and the package LaTeX preamble
- TeX gallery/debug validation assets

Upstream-owned behavior:

- Matplotlib figure cloning, panel isolation, cleanup, target-supplied font
  replacement, styling, callbacks, and rasterization live in `pubify-mpl`.

## Public Surface

Supported package-root imports:

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

## Dependency Direction

`pubify-tex` depends on `pubify-mpl`. `pubify-mpl` must not depend on
`pubify-tex`.
