---
title: "Contributing"
status: active
---

# Contributing

## Add a new bank skill
1) Create `skills/<skill-name>/SKILL.md`.
2) Keep `SKILL.md` concise; move large content into `references/`.
3) Add `scripts/` only when deterministic behavior is needed.
4) Update `catalog/skillsets.json` if the skill is part of a baseline or language set.
5) Run local checks (see below) before committing.

## Local checks (uv + prek)
1) Install `uv` and `prek`:
   - `uv tool install prek` (or run once via `uvx prek`)
2) Run all checks:
   - `uvx prek run --all-files`
3) Optional: install the git hook:
   - `prek install`
4) Hooks live in `.pre-commit-config.yaml` and run:
   - `scripts/validate_registry.py`
   - `scripts/smoke_bootstrap.py`

## Add/modify overlay templates
- Edit files under `templates/`.
- Keep templates stable and backward-compatible where possible (overlays may be project-owned).

## Update `project-bootstrap`
- Edit `skills/project-bootstrap/scripts/bootstrap.py`.
- Maintain idempotency:
  - never silently clobber modified overlays,
  - only remove stale bank skills previously installed by bootstrap,
  - write all decisions into `.agent/skills_todo.md` when uncertain.
