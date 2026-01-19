---
title: "Bootstrap: Usage and Update Guide"
status: active
---

# Bootstrap: Usage and Update Guide

This repo provides the `project-bootstrap` skill which installs/generates repo-scoped skills for both Codex and Claude.
The CLI subcommand is `init`, but the process is designed to be repeatable.

## What bootstrap does
1) Clones/updates the trusted registry into `.agent/skillregistry`.
2) Detects stack (languages, Docker, CI) and basic API hints.
3) Selects bank skills from `catalog/skillsets.json`.
4) Installs bank skills into `.codex/skills` and `.claude/skills`.
5) Generates overlays (`project-workflow`, `api-*`) safely.
6) Writes state and TODO artifacts under `.agent/`.

## One-time: install `project-bootstrap` globally
Copy the folder `skills/project-bootstrap/` into:
- Codex: `~/.codex/skills/project-bootstrap/`
- Claude: `~/.claude/skills/project-bootstrap/`

Restart the CLI after installation.

## Run bootstrap in a project repo
From the project root:

```bash
python3 .agent/skillregistry/skills/project-bootstrap/scripts/bootstrap.py init \
  --skillregistry-git <GIT_URL_OR_LOCAL_PATH> \
  --skillregistry-ref <REF> \
  --targets codex,claude
```

You can also set:
- `SKILLREGISTRY_GIT`
- `SKILLREGISTRY_REF` (default `main`)

Targets:
- `--targets codex,claude` (default)

## What bootstrap writes
- `.agent/skillregistry/` (cloned registry)
- `.agent/project_profile.json`
- `.agent/skills_state.json`
- `.agent/skills_todo.md`
- `.agent/overlays_pending/` (only when overlays were modified)
- `.codex/skills/*` (bank skills + overlays)
- `.claude/skills/*` (bank skills + overlays)

## Overlay update policy (default)
Overlays are updated only if unchanged since last generation:
- If unchanged: overwrite in place.
- If modified: do not overwrite; write candidate to `.agent/overlays_pending/...` and add TODO.
- If no generation history: do not overwrite unless explicitly adopted.

Flags:
- `--force-overwrite-overlays`: overwrite overlays even if modified (writes `SKILL.md.bootstrap.bak`).
- `--adopt-existing-overlays`: if an overlay exists but has no generation history, adopt it as baseline.

## Clean-up behavior
On rerun, bootstrap removes only stale bank skills it previously installed that are no longer selected (based on `.agent/skills_state.json`), then re-copies the currently selected bank skills.

Disable cleanup with:
- `--no-clean-stale-bank-skills`

## Empty project behavior
If no stack signals are detected, bootstrap installs only the baseline skills.
`project-workflow` is still generated, and commands will include TODO markers.

## Security
Bootstrap only installs skills from the trusted registry you provide.
See `docs/SECURITY.md` for supply-chain guardrails.

## Troubleshooting
- If Codex doesn’t see new skills: restart Codex (required in common setups).
- If overlays don’t update: check `.agent/skills_state.json` for `overlay_generated_hashes`, and `.agent/overlays_pending/` for candidates.
