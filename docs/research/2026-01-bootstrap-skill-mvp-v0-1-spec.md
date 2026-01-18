---
title: "Bootstrap Skill MVP v0.1: Definition of Done and Reference Spec"
date: 2026-01
tags: [skills, bootstrap, codex-cli, claude-code, skill-registry, overlays, manifests]
status: draft
notes:
  - "Structured English rewrite of a Russian MVP spec."
---

# Bootstrap Skill MVP v0.1: Definition of Done and Reference Spec

## Definition of Done (DoD)
After running bootstrap inside a project repository, the following artifacts exist:

### Project state
- `.agent/skillbank/` — a clone of the trusted bank pinned to a specific `ref`/commit.
- `.agent/project_profile.json` — detected project signals (stack, tooling, APIs).
- `.agent/skills_state.json` — what was installed/generated, plus bank origin (`git`, `ref`, `commit`).
- `.agent/skills_todo.md` — unresolved items that require human input.

### Skills installed (both runtimes)
- `.codex/skills/` — selected “bank skills” (copied into the repo) + generated overlay skills.
- `.claude/skills/` — same set of copied bank skills + generated overlay skills.

### Required overlay skills
- `project-workflow` overlay is always created (canonical `build/test/lint/run` + DoD).
- If external APIs are detected: create `api-<name>` overlays at least as skeletons + TODO.

## Step 1: Standardize the bank repository layout
Target structure:
```
skillbank/
  skills/
    project-bootstrap/
      SKILL.md
      scripts/
        bootstrap.py
    lang-go/
      SKILL.md
    lang-rust/
      SKILL.md
    lang-python/
      SKILL.md
    lang-ts/
      SKILL.md
    tdd-loop/
      SKILL.md
    code-review/
      SKILL.md
    api-openapi-generic/
      SKILL.md
  templates/
    project-workflow.SKILL.template.md
    api-skeleton.SKILL.template.md
  catalog/
    skillsets.json
```

Bank rule:
- “General practice” lives in `skills/<name>/SKILL.md`.
- “Project-generated content” comes from `templates/*` and is materialized as overlay skills.
- Do not embed large specs/logs in `SKILL.md`; store them under `references/` in overlays.

## Step 2: Define baseline skillsets
Minimal `catalog/skillsets.json`:
```json
{
  "baseline": ["tdd-loop", "code-review", "api-openapi-generic"],
  "lang_go": ["lang-go"],
  "lang_rust": ["lang-rust"],
  "lang_python": ["lang-python"],
  "lang_ts": ["lang-ts"]
}
```

## Step 3: Bootstrap skill contract (`project-bootstrap/SKILL.md`)
Frontmatter:
- `name: project-bootstrap`
- `description`: detect stack, install baseline + language skills into `.codex/skills` and `.claude/skills`, generate overlays (`project-workflow`, `api-<name>`), write `.agent/*` state.

Inputs:
- `SKILLBANK_GIT` (required): git URL of the trusted bank repo.
- `SKILLBANK_REF` (default `main`): branch/tag/commit.

Required behavior:
1) Clone or update `.agent/skillbank` at `SKILLBANK_GIT` + `SKILLBANK_REF`.
2) Run:
   - `python3 .agent/skillbank/skills/project-bootstrap/scripts/bootstrap.py init`
3) Print next steps:
   - restart Codex if needed
   - review `.agent/skills_todo.md`

Constraints:
- install only from the trusted bank,
- treat bank skills as read-only; project-specific content goes into overlays.

## Step 4: `bootstrap.py` MVP behavior
File: `skills/project-bootstrap/scripts/bootstrap.py`

### Core operations
- Determine repo root (via `git rev-parse --show-toplevel`, fallback to CWD).
- Detect project:
  - languages: `go.mod`, `Cargo.toml`, `pyproject.toml`/`requirements.txt`, `package.json`
  - infra: Docker files, `.github/workflows`
  - external APIs: heuristics based on env/config keys like `*_API_KEY`, `*_BASE_URL`
  - OpenAPI/Swagger local files: `openapi.*`, `swagger.*`
- Infer canonical commands:
  - prefer `Taskfile.yml`, `justfile`, `Makefile`
  - else language defaults (with TODO placeholders where uncertain)
- Load `catalog/skillsets.json` and select bank skills: `baseline` + language-specific additions.
- Install selected bank skills (copy folders) into:
  - `.codex/skills/<skill>/`
  - `.claude/skills/<skill>/`
- Generate overlays into both runtimes:
  - `project-workflow/` from `templates/project-workflow.SKILL.template.md`
  - `api-<name>/` skeletons from `templates/api-skeleton.SKILL.template.md` (+ `references/TODO.md`)
- Write `.agent/project_profile.json`, `.agent/skills_state.json`, `.agent/skills_todo.md`.

### CLI interface
`bootstrap.py init` supports:
- `--targets codex,claude` (default both)
- `--skillbank-git` or env `SKILLBANK_GIT` (required)
- `--skillbank-ref` or env `SKILLBANK_REF` (default `main`)

## Step 5: Overlay templates

### `templates/project-workflow.SKILL.template.md`
Defines canonical commands (`{{BUILD_CMD}}`, `{{TEST_CMD}}`, `{{LINT_CMD}}`, `{{RUN_CMD}}`) and a Definition of Done.

### `templates/api-skeleton.SKILL.template.md`
Defines an `api-{{API_NAME}}` skill skeleton plus a `references/TODO.md` pointer.

## Step 6: One-time global install of `project-bootstrap`
One manual step: copy the `project-bootstrap/` skill folder into:
- `~/.codex/skills/project-bootstrap/`
- `~/.claude/skills/project-bootstrap/`

## Step 7: Run bootstrap in a project
In the project repo root:
- set `SKILLBANK_GIT` and optional `SKILLBANK_REF`
- run bootstrap (via the skill’s documented procedure), which executes:
  - clone/update `.agent/skillbank`
  - `python3 .agent/skillbank/skills/project-bootstrap/scripts/bootstrap.py init`

## Step 8: Update to the latest bank version
Re-run `init` with a newer `SKILLBANK_REF`:
```bash
python3 .agent/skillbank/skills/project-bootstrap/scripts/bootstrap.py init \
  --skillbank-git <git-url> \
  --skillbank-ref <ref>
```

Rationale:
- bank skills are treated as read-only and can be re-copied,
- project-specific knowledge is captured in overlays (`project-workflow`, `api-*`).

## Step 9 (future): Claude enhancements
After v0.1 is proven, extend materialization to include:
- `.claude/hooks` for error logging and session retros (without bloating context),
- a `postmortem` subagent that runs in an isolated context,
- “lessons learned” stored as project-owned overlays or references.

