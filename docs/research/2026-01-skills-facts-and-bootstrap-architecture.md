---
title: "Skills: Ground Truth Facts and a Bootstrap-Orchestrator Architecture"
date: 2026-01
tags: [skills, codex-cli, claude-code, bootstrap, skill-registry, supply-chain, manifests]
status: draft
---

# Skills: Ground Truth Facts and a Bootstrap-Orchestrator Architecture

## Facts we can rely on (practical constraints)

### Codex CLI (OpenAI)
- A skill is a **folder** containing `SKILL.md` (optionally `scripts/`, `references/`, `assets/`).
- **Progressive disclosure**: on startup, Codex loads only `name` + `description`; the body is loaded when the skill triggers.
- Skills can be **repo-scoped** (`.codex/skills/...`) and/or **user-scoped** (`~/.codex/skills/...`), with priority/scope rules. Skill folders may be symlinks.
- After adding/updating skills, a **Codex restart is commonly required** to reload the skill registry.
- There are built-in system skills like `skill-creator` and `skill-installer`.
- In some versions, skills may be behind a feature flag (e.g., `codex --enable skills`).

### Claude Code (Anthropic)
- A skill is centered on `SKILL.md` (YAML frontmatter + instructions); metadata loads first, full body later.
- Skills can be **personal** (`~/.claude/skills/`) and **project** (`.claude/skills/`), with priority rules; enterprise/plugin distribution may exist.
- Claude Code supports additional controls often referenced in skill design:
  - `allowed-tools` (constrain what the skill may use),
  - `context: fork` (run in an isolated sub-context),
  - hooks (e.g., `PreToolUse`, `PostToolUse`, `Stop`) to enforce guardrails.

### Security reality
Skills/plugins are a **supply-chain surface**:
- treat skill sources as untrusted by default,
- prefer a curated registry and allowlists,
- constrain tools for “reader” skills (and be cautious with executable scripts).

## Goal: one bootstrap skill that creates the rest
The durable pattern is: keep one small, stable “orchestrator” skill and let it **materialize** the rest of the repo’s skill foundation.

### Why this works
- The bootstrap skill does not need deep domain knowledge; it needs **repeatable mechanics**.
- Project-specific knowledge lives in **overlay skills** generated into the repo.
- Large specs/logs are stored in `references/` and accessed on-demand (avoid context bloat).

## Architecture: Registry + Bootstrap + Manifests

### 1) Skill registry (trusted, read-only source of templates)
Example layout:
```
skillregistry/
  skills/
    lang-go/
    lang-rust/
    lang-python/
    lang-ts/
    api-openapi-generic/
    testing-tdd-loop/
    ci-github-actions/
    code-review-checklist/
```
Guideline: keep `SKILL.md` lean; move large docs/specs into `references/` and provide scripts for selective extraction when needed.

### 2) Repo-scoped skills (generated/installed into the project)
Bootstrap materializes:
- `.codex/skills/...`
- `.claude/skills/...`
Plus state:
- `.agent/project_profile.yaml`
- `.agent/skills_plan.yaml`
- `.agent/skills_todo.md`

### 3) Manifests and lockfiles (repeatability)
- `skills_plan.yaml`: “what we need and why” (bootstrap output).
- `skills.lock`: “where it came from” (registry URL + commit SHA + template paths).

This enables safe updates: update registry ref, re-run bootstrap, review diffs.

## Two-phase bootstrap algorithm

### Phase A: Detect & Plan
Scan the repo to infer:
- **languages**: `go.mod`, `Cargo.toml`, `pyproject.toml`/`requirements.txt`, `package.json` (+ `tsconfig`)
- **workflow commands**: `Makefile`, `Taskfile.yml`, `justfile`, package scripts, `.github/workflows`, `docker-compose.yml`
- **external APIs**: `.env.example`, config files, URLs/domains, local OpenAPI/Swagger/GraphQL schema files

Output:
- `skills_plan.yaml` listing required skills (template vs generated) and reasons
- `skills_todo.md` for unresolved items (missing lint command, missing API docs, etc.)

### Phase B: Materialize
For each plan item:
1) **Template skills**: copy from the trusted registry into `.codex/skills/<name>/` and `.claude/skills/<name>/`.
2) **Overlay skills** (project-owned):
   - `project-workflow` (canonical `build/test/lint/run` + DoD)
   - language conventions overlays (e.g., `project-go-conventions`)
   - `api-<service>` skills (project integration notes)
3) **API skill generation**:
   - if local OpenAPI exists: store it in `references/` and provide a query script (do not paste the whole spec into `SKILL.md`)
   - else: generate a skeleton with `references/TODO.md` listing what’s missing (base URL, auth, rate limits, idempotency, retries/timeouts)

Finally:
- For Codex: instruct a **restart** to ensure newly written repo skills are loaded.
- For Claude: still include a verification step (“confirm new skills are discoverable”), even if hot-reload works.

## Make it “ironclad”: reliability additions
- **Idempotency**: re-running bootstrap should converge (avoid duplicate junk; only update what is owned by bootstrap).
- **No silent overwrites of overlays**: default to “create if missing”; require an explicit `--force-overwrite-overlays` to regenerate project-owned skills.
- **Safe cleanup**: remove stale template skills previously installed by bootstrap (based on `skills.lock` / state), without touching unrelated directories.
- **Allowlist sources**: only pull templates from trusted registry URLs; never “install from random GitHub”.
- **Tool restrictions**: for template/reader skills, restrict tools (`allowed-tools`) and avoid executable scripts unless necessary.

## Recommended `project-bootstrap` skill shape (portable “YAML superset”)
You can treat the YAML frontmatter as a superset: Codex ignores unknown fields; Claude may use them.
Include:
- `context: fork` (to isolate the bootstrap workflow)
- `allowed-tools` (to constrain capability surface)
- strict constraints about never embedding large specs/logs in the skill body

