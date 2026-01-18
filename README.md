# skillregistry (trusted)

This repository is a trusted internal registry of agent skills.

## Structure
- `skills/<skill-name>/SKILL.md`
- `templates/` for generating project overlays
- `catalog/skillsets.json` for bootstrap selection

## Bootstrap usage (inside a project repo)

```bash
python3 .agent/skillregistry/skills/project-bootstrap/scripts/bootstrap.py init \
  --skillregistry-git <GIT_OR_PATH> \
  --skillregistry-ref <REF>
```

Overlays are safe-updated: overwritten only if unchanged since last generation.
Use `--force-overwrite-overlays` to overwrite anyway.

