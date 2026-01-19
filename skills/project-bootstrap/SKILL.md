---
name: project-bootstrap
description: >
  Bootstraps a repository with project skills from the trusted internal skillregistry.
  Detect stack, install baseline + language skills into .codex/skills and .claude/skills,
  generate project-specific overlay skills (project-workflow, api-<name>) and write plans/state into .agent/.
---

# Project Bootstrap (v0.1)

## Required inputs
- `SKILLREGISTRY_GIT`: git URL or local path to the trusted skillregistry repo
- `SKILLREGISTRY_REF`: branch/tag/commit (default: `main`)

## What this skill must do
1) Ensure `.agent/skillregistry` exists by cloning `SKILLREGISTRY_GIT` and checking out `SKILLREGISTRY_REF`.
2) Run:
   `python3 .agent/skillregistry/skills/project-bootstrap/scripts/bootstrap.py init`
   with:
   - `--skillregistry-git`
   - `--skillregistry-ref`
3) After init, print next steps:
   - review `.agent/skills_todo.md`
   - restart Codex CLI to ensure skills are reloaded (recommended)

## Constraints
- Install only from the trusted skillregistry.
- Never fetch skills from external catalogs.
- Treat installed registry skills as read-only; project customizations go into overlay skills.
- Never overwrite overlay skills silently unless the overlay is unchanged (safe overwrite policy) or `--force-overwrite-overlays`.
