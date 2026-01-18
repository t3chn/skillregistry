---
title: "Security Model"
status: active
---

# Security Model

## Threat model
Skills and plugins influence agent behavior and may execute scripts. Treat them as a supply-chain surface.

## Trusted sources (policy)
- Bootstrap must install templates only from an allowlisted `skillregistry` (Git URL or local path).
- Do not fetch skills from public catalogs as part of bootstrap.

## Script-backed skills
- Prefer instruction-only skills.
- If scripts are required:
  - keep them minimal and deterministic,
  - avoid network access unless explicitly required and reviewed,
  - avoid executing arbitrary shell commands constructed from untrusted input.

## Large artifacts
- Never paste large logs/specs into `SKILL.md`.
- Store them under `references/` and link to them.

## Project hygiene (recommendation)
In consuming project repos, ignore:
- `.agent/skillregistry/`
- `.agent/project_profile.json`
- `.agent/skills_state.json`
- `.agent/skills_todo.md`
- `.agent/overlays_pending/`

Commit project-owned overlays if desired (`project-workflow`, `api-*`).
