# skillregistry (trusted)

This repository is a trusted internal registry of agent skills.

Design notes and history are tracked in beads; this repo stays “runtime-minimal”.

## Docs
- `docs/PRD.md` for the canonical spec
- `docs/BOOTSTRAP.md` for usage and update policy
- `docs/SECURITY.md` for supply-chain guardrails
- `docs/CONTRIBUTING.md` for adding skills and local checks

## Structure
- `skills/<skill-name>/SKILL.md`
- `templates/` for generating project overlays
- `catalog/skillsets.json` for bootstrap selection

## Quickstart (project bootstrap)
1) Install `project-bootstrap` globally:
   - Codex: `~/.codex/skills/project-bootstrap/`
   - Claude: `~/.claude/skills/project-bootstrap/`
2) Run bootstrap inside a project repo:

```bash
python3 .agent/skillregistry/skills/project-bootstrap/scripts/bootstrap.py init \
  --skillregistry-git <GIT_OR_PATH> \
  --skillregistry-ref <REF>
```

Bootstrap is safe to re-run: bank skills update, overlays are protected.
Overlays are overwritten only if unchanged since last generation.
Use `--force-overwrite-overlays` to overwrite anyway.

See `docs/BOOTSTRAP.md` for the full flow and `docs/PRD.md` for the canonical spec.
