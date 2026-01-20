---
title: "Bootstrap: Usage and Update Guide"
status: active
---

# Bootstrap: Usage and Update Guide

This repo provides the `project-bootstrap` skill which installs/generates repo-scoped skills for Codex (Claude is currently skipped).
The CLI subcommand is `init`, but the process is designed to be repeatable.

## What bootstrap does
1) Clones/updates the trusted registry into `.agent/skillregistry`.
2) Detects stack (languages, Docker, CI) and basic API hints.
3) Selects registry skills from `catalog/skillsets.json`.
4) Installs registry skills into `.codex/skills` (Claude target is skipped with a TODO).
5) Generates overlays (`<prefix>-project-workflow`, `<prefix>-api-*`) safely.
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
- `--targets codex,claude` (default; claude is currently skipped)

Install method:
- `--install-method skill-installer` (default; uses system skill-installer)
- `--install-method local` (local copy, useful for tests/offline)

Registry flags:
- `--force-overwrite-registry-skills` (overwrite registry skills if they already exist)

## What bootstrap writes
- `.agent/skillregistry/` (cloned registry)
- `.agent/project_profile.json`
- `.agent/skills_state.json`
- `.agent/skills_todo.md`
- `.agent/overlays_pending/` (only when overlays were modified)
- `.codex/skills/*` (registry skills + prefixed overlays)
- `.claude/skills/*` (currently skipped; placeholder for future support)

## Overlay update policy (default)
Overlays are updated only if unchanged since last generation:
- If unchanged: overwrite in place.
- If modified: do not overwrite; write candidate to `.agent/overlays_pending/...` and add TODO.
- If no generation history: do not overwrite unless explicitly adopted.

Overlay names are prefixed (`<prefix>-project-workflow`, `<prefix>-api-*`). The prefix is derived from the project root name (3–4 chars of the slug) unless overridden with `--project-prefix`.
If a similar overlay exists (e.g., `project-workflow`, `*-project-workflow`, `api-foo`, `*-api-foo`), bootstrap skips creation unless `--force-create-overlays` is set or the prefix changed. When the prefix changes, existing overlays are not renamed; a TODO is written for manual migration.

Flags:
- `--force-overwrite-overlays`: overwrite overlays even if modified (writes `SKILL.md.bootstrap.bak`).
- `--force-create-overlays`: create overlays even if a similar overlay exists.
- `--adopt-existing-overlays`: if an overlay exists but has no generation history, adopt it as baseline.
- `--project-prefix`: override the project prefix used for overlays.

## Clean-up behavior
On rerun, bootstrap removes only stale registry skills it previously installed that are no longer selected (based on `.agent/skills_state.json`), then re-copies the currently selected registry skills.

Disable cleanup with:
- `--no-clean-stale-registry-skills`

## Empty project behavior
If no stack signals are detected, bootstrap installs only the baseline skills.
`<prefix>-project-workflow` is still generated, and commands will include TODO markers.

## Security
Bootstrap only installs skills from the trusted registry you provide.
See `docs/SECURITY.md` for supply-chain guardrails.

## Troubleshooting
- If Codex doesn’t see new skills: restart Codex (required in common setups).
- If overlays don’t update: check `.agent/skills_state.json` for `overlay_generated_hashes`, and `.agent/overlays_pending/` for candidates.
