# Development

Create or refresh the local environment with:

```bash
conda create -p ./.conda python=3.12 pip -y
./.conda/bin/pip install -e ".[dev]"
```

Run tests with:

```bash
./.conda/bin/pytest tests -q
```

Build docs with:

```bash
./.conda/bin/mkdocs build --strict
```

## TeX Debug Workflow

For TeX-side behavior changes, stage the debug workspace before compiling.

```bash
./.conda/bin/python scripts/build_tex_assets.py debug/debug-subcaptions.tex
cd build/tex
latexmk -g -pdf -interaction=nonstopmode debug-subcaptions.tex
```

Use `build/tex/` as the working directory so generated `.tex`, `.aux`, `.fls`,
`.fdb_latexmk`, and `.log` files stay together. If `latexmk` is not available,
complete the Python and docs checks and record that TeX compile validation was
not run.
