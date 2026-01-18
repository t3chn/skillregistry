---
title: "skillregistry PRD"
status: active
---

# skillregistry (trusted) — PRD

## Purpose
Provide a **trusted, Git-governed source of agent skills** used by OpenAI Codex CLI and Claude Code.

The registry is designed to be:
- small and reproducible,
- safe to clone into projects,
- easy to update via git refs,
- friendly to project-specific customization via overlays (without breaking updates).

## Non-goals
- A public marketplace or external catalog integration.
- Storing long research notes in this repo (tracked in beads instead).

## Repository layout (runtime-only)
- `skills/<skill-name>/SKILL.md` (+ optional `scripts/`, `references/`, `assets/`)
- `templates/` — templates for generated project overlays
- `catalog/skillsets.json` — baseline + language mappings for bootstrap selection
- `docs/PRD.md` — this document (single canonical doc)

## Core rules
1) **Trusted sources only**: bootstrap installs skills only from this registry (allowlist).
2) **Bank skills are read-only**: treat copied template skills as replaceable.
3) **Project customization lives in overlays**: `project-workflow`, `api-*`, and other project-owned skills.
4) **No large blobs in `SKILL.md`**: store large specs/logs under `references/` and link to them.

## Bootstrap: MVP v0.1 contract
The `project-bootstrap` skill orchestrates:
1) Clone/update registry into `.agent/skillregistry` at a specific ref/commit.
2) Detect stack and workflow commands.
3) Install selected bank skills into:
   - `.codex/skills/<skill>/`
   - `.claude/skills/<skill>/`
4) Generate overlays into both:
   - `project-workflow`
   - `api-<name>` (if external APIs detected)
5) Write project state:
   - `.agent/project_profile.json`
   - `.agent/skills_state.json`
   - `.agent/skills_todo.md`

## Overlay update policy (default = C)
Overlays are updated safely:
- **Overwrite only if unchanged** since the last generation (compare `generated_hash` stored in `.agent/skills_state.json`).
- If an overlay was modified: **do not overwrite**; write a candidate to `.agent/overlays_pending/<target>/<overlay>/SKILL.md` and add a TODO.
- If there is no generation history: **do not overwrite** (safe fallback), unless explicitly adopted.

Flags:
- `--force-overwrite-overlays`: overwrite overlays even if modified (writes a backup).
- `--adopt-existing-overlays`: if overlay exists but has no generation history, adopt current as baseline.

## Bank skills lifecycle
- On bootstrap rerun, remove only stale bank skills that were previously installed by bootstrap but are no longer selected (based on prior `.agent/skills_state.json`).
- Re-copy selected bank skills on each run (bank skills are treated as replaceable).

## Project git hygiene (recommendation)
In a target project repo:
- Commit overlays (`project-workflow`, `api-*`) if you want them reviewed/owned by the project.
- Ignore `.agent/skillregistry` and volatile state (profile/state/todo/pending candidates).

## Security posture
Skills/plugins are supply-chain surface:
- enforce allowlisted registry sources,
- review script-backed skills,
- keep skills minimal; prefer instruction-only skills unless a script is necessary.

