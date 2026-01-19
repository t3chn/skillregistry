# Design: Bootstrap installer and overlay prefixing

## Goals
- Install registry skills using the system skill-installer by default.
- Keep registry skills safe: do not overwrite existing directories unless explicitly forced.
- Add project-specific overlay prefixes to avoid name collisions across projects.
- Preserve manual edits in overlays and avoid unintended renames.
- Keep tests stable by allowing a local install method.

## Non-goals
- Claude installation support (tracked as a TODO for now).
- Auto-merge of overlay changes beyond current safe-write policy.

## Decisions
- Add `--install-method` with values `skill-installer|local`, default `skill-installer`.
- Add `--force-overwrite-registry-skills` to replace existing registry skills.
- Add `project_prefix` derived from project root name (first 3-4 characters of slug); allow override via `--project-prefix` and persist in state.
- Overlay names become `<prefix>-project-workflow` and `<prefix>-api-<name>`; front-matter `name` matches the directory name.
- Similar-overlay rule applies only to overlays: skip creation if any existing overlay directory shares the same base name without prefix (e.g., `project-workflow`, `*-project-workflow`, `api-foo`, `*-api-foo`).
- If prefix changes, do not rename existing overlays. Create new overlays and add a TODO for manual migration.
- Targets: skip `claude` installs and overlay generation, record TODO and `unsupported_targets` in state.

## Architecture
- `bootstrap.py` keeps cloning `.agent/skillregistry` to read `catalog/skillsets.json` and templates.
- New helper script `scripts/install_registry_skills.py` wraps the system skill-installer:
  - Calls `~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py`.
  - Uses `--repo t3chn/skillregistry --ref <ref> --path skills/<name> --dest <project>/.codex/skills`.
  - Skips install if destination exists (unless `--force-overwrite-registry-skills`).
  - Writes TODO entries for skipped installs.
- `bootstrap.py` controls method selection and state updates.

## Data flow
1. Detect project, infer commands, select registry skills.
2. Determine `project_prefix` (state or auto). If `--project-prefix` given, update state.
3. Install registry skills:
   - `skill-installer` method for `codex` target (default), or `local` copy for tests/offline.
   - Respect `--force-overwrite-registry-skills`.
4. Generate overlays for supported targets only:
   - Check similar overlays; skip unless `--force-create-overlays` or prefix explicitly changed.
   - Use safe-write policy with hashes for updates.
5. Write state and TODO artifacts.

## State changes
`skills_state.json` adds:
- `project_prefix`
- `install_method`
- `registry_skills_selected`
- `registry_skills_installed`
- `registry_skills_skipped` (name + reason)
- `unsupported_targets`
- `overlays_skipped`

## Error handling
- If skill-installer script is missing, emit a clear error and suggest `--install-method local`.
- If target is unsupported (claude), add TODO and continue.
- If a registry skill path does not exist in the registry, add TODO and continue.

## Tests
- Extend unit tests for overlay name/prefix and similar-overlay detection.
- Integration tests use `--install-method local` to avoid network.
- Negative tests: existing registry skill directory should be skipped unless forced; similar overlay should block creation unless forced.
