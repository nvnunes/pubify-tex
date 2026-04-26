# Testing

Use the repo-local `./.conda` environment for Python commands unless a task
explicitly requires something else.

## Canonical Verification Commands

```bash
./.conda/bin/pytest tests -q
./.conda/bin/mkdocs build --strict
```

Changes to TeX-side behavior should also be validated from a staged TeX
workspace when LaTeX is available. Follow the staged workflow in
`docs/development.md`.
