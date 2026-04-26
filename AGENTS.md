# AGENTS.md

## Astro-Agents Bootstrap
- Use `astro-agents` for reusable authoring, review, and routing guidance in this repo.

## Scope
- Documentation surface profile: public-python.

## Source Of Truth Docs
- Follow `README.md` for the public overview and starting examples.
- Follow `docs/architecture.md` for package boundaries, public API contracts, and TeX asset ownership.
- Follow `docs/testing.md` for canonical verification commands and completion expectations.
- Follow `docs/development.md` for local setup and TeX debug workflow.

## Shared Guidance
- Use `astro-agents/guidance/agent-surface.md` for shared agent-surface guidance.
- Use `astro-agents/guidance/public-python-projects.md` for shared public Python repo guidance.
- Use `astro-agents/guidance/python-development.md` for shared Python architecture, coding-policy, and development-workflow guidance.

## Authoring Requirements
- For Python code, follow `astro-agents/authoring/code/python.md`.
- For repo docs, follow `astro-agents/authoring/writing/repo-docs.md`.
- For `README.md`, follow `astro-agents/authoring/writing/readme-md.md` in addition to repo-docs guidance.

## Working Rules
- Keep this package focused on LaTeX layout, TeX assets, and LaTeX-aware figure export.
- Matplotlib-only figure preparation belongs in `pubify-mpl`.
- Before concluding substantial work, satisfy the verification expectations in `docs/testing.md`.
