# AGENTS.md

## Scope
- Documentation surface profile: public-python.

## Source Of Truth Docs
- Follow `README.md` for the public overview and starting examples.
- Follow `docs/architecture.md` for package boundaries, public API contracts, and TeX asset ownership.
- Follow `docs/testing.md` for canonical verification commands and completion expectations.
- Follow `docs/development.md` for local setup and TeX debug workflow.

## Shared Validation
- Use `$agent-surface-review` for shared agent-surface review.
- Use `$documentation-surface-review` for documentation-surface review with the `public-python` profile.
- Use `$code-quality-review` for source-code quality review.

## Skill Requirements
- For Python code, use `$python-code-writing`.
- For project docs such as `docs/architecture.md`, `docs/testing.md`, `docs/development.md`, and similar long-lived project documents, use `$project-docs-writing`.
- For `README.md`, use `$readme-writing`.
- For plan documents or phased execution docs when they are created or revised, use `$plan-writing`.

## Astro-Agents Integration
- `astro-agents` owns the shared `$pubify-authoring` skill used by agents working on downstream pubify publication and presentation workflows.
- When this project changes user-facing `pubify-tex` behavior, update the corresponding `astro-agents` skill references: `skills/pubify-authoring/references/pubify-pubs.md`, `skills/pubify-authoring/references/pubify-pubs-figures.md`, and `skills/pubify-authoring/references/figure-export.md` when needed.
- Examples that require an `astro-agents` update include LaTeX layout behavior, `\figprintlayoutspec`, template schema, figure layouts, TeX asset ownership, generated TeX artifact behavior, and LaTeX-aware figure export semantics.

## Working Rules
- Keep this package focused on LaTeX layout, TeX assets, and LaTeX-aware figure export.
- Matplotlib-only figure preparation belongs in `pubify-mpl`.
- Before concluding substantial work, satisfy the verification expectations in `docs/testing.md`.
