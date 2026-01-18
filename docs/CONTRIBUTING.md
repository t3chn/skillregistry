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

## Add/modify overlay templates
- Edit files under `templates/`.
- Keep templates stable and backward-compatible where possible (overlays may be project-owned).

## Update `project-bootstrap`
- Edit `skills/project-bootstrap/scripts/bootstrap.py`.
- Maintain idempotency:
  - never silently clobber modified overlays,
  - only remove stale bank skills previously installed by bootstrap,
  - write all decisions into `.agent/skills_todo.md` when uncertain.

