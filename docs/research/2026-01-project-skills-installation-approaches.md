---
title: "Convenient Installation of Project Skills in OpenAI Codex and Claude Code"
date: 2026-01
tags: [skills, codex-cli, claude-code, installation, manifest, updates, supply-chain]
status: draft
open_questions:
  - "Add primary sources for: 'Agent Skills standard' timeline, SkillsMP numbers/API, Claude marketplace.json behavior."
---

# Convenient Installation of Project Skills in OpenAI Codex and Claude Code

## Context: a shared “Agent Skills” format
Project “skills” are extensions for coding agents (OpenAI Codex CLI, Anthropic Claude Code) packaged as a folder containing `SKILL.md` (metadata + instructions) and optionally `scripts/`, `references/`, and `assets/`.

Because both tools can consume the same basic format, teams want one repeatable way to:
- select a safe subset of skills for a project,
- install them “all at once”,
- update them over time,
- allow project-specific customization without breaking upstream updates.

## Requirements for a good solution
- **One workflow for both agents** (Codex + Claude), not two separate systems.
- **Batch install** from a list/manifest (“one command”).
- **Automation-first** (a CLI tool/script rather than manual copying).
- **Update story** (pull new versions, optionally pinned to commits).
- **Customization** (local overlays/forks without losing updateability).
- **Extensibility** (later: subagents, hooks, environments/deps).
- (Optional) **Catalog UX** (browse/search what’s available to the team).

## Existing installation approaches (today)

### Manual install from GitHub
Copy/clone a skill folder into:
- Claude: `~/.claude/skills/` (personal) or `.claude/skills/` (project)
- Codex: `~/.codex/skills/` (personal) or `.codex/skills/` (project)

Pros: simple, transparent.  
Cons: tedious at scale; updates and version drift are painful.

### Codex CLI: built-in installer (`skill-installer`)
Codex includes a system skill that can install skills from curated lists or GitHub paths.

Pros: great for Codex-only workflows; reduces manual steps.  
Cons: not a universal cross-tool solution by itself; still needs a Claude story.

### Claude Code: marketplace / plugin-like installs
Some ecosystems support a “marketplace” metadata file (e.g., `marketplace.json`) to enable one-command install.

Pros: convenient when available.  
Cons: coverage is incomplete; may depend on specific distribution channels.

### SkillsMP and community catalogs
SkillsMP and similar catalogs help discovery/search across many repos.

Pros: good discovery UX.  
Cons: discovery ≠ installation; supply-chain risk if used indiscriminately.

### Community CLIs (e.g., x-cmd-like tooling)
Some community tools aim to unify search + install + update across agents.

Pros: closest to “one tool for everything”.  
Cons: introduces another supply-chain dependency; may not match internal trust requirements.

## Recommended baseline: manifest + trusted registry + installer CLI
The most robust pattern is:
1) keep a **project manifest** that declares required skills and sources,  
2) use a **single CLI installer** that materializes them into both `.codex/skills/` and `.claude/skills/`,  
3) support **updates** via pinned refs (lockfile) and safe re-sync,  
4) keep project changes in **overlays** to avoid merge pain.

### 1) Skills manifest (“requirements.txt for skills”)
Add a file like `skills.yaml` (or `.agent/skills_plan.yaml`) that lists:
- skill name,
- source (trusted registry URL/repo path),
- version pin (branch/tag/commit),
- install scope (project/global),
- optional “overlay” markers (generated vs editable).

This provides:
- reproducibility,
- easy batch install,
- clear team visibility (“what skills does this project rely on?”).

### 2) Installer CLI behavior
An installer script (internal) should:
- read the manifest,
- fetch the referenced skills (git clone/sparse checkout or archive download),
- install into `.claude/skills/<skill>/` and `.codex/skills/<skill>/`,
- record a lock (`skills.lock`) with the exact source + commit,
- warn on name collisions,
- optionally create symlinks instead of duplicating files (if both agents support symlinked directories in your environment).

### 3) Updates
Support two modes:
- **Floating**: track a branch (fast, less reproducible).
- **Pinned**: lock to a commit SHA (reproducible; updates are explicit).

Recommended default: pinned with an explicit “update” command that:
- refreshes registry refs,
- produces a diff of what would change,
- updates lockfile,
- re-materializes templates without clobbering project-owned overlays.

### 4) Customization strategy (avoid “local edits inside templates”)
To keep updates safe:
- treat imported template skills as **read-only**,
- store project-specific rules in **overlay skills** (e.g., `project-workflow`, `project-<lang>-conventions`, `api-<service>`),
- require explicit flags to overwrite overlays (never silently clobber).

## Practical details and guardrails

### Dependencies and environments
Some skills rely on Python/Node tools.
An installer can optionally:
- create a project venv (or use an existing one),
- install shared dependencies declared in the manifest,
- chmod `+x` scripts when needed,
- otherwise emit a “deps TODO” with exact install commands.

### Expand beyond skills: hooks and subagents
Design the manifest format to allow additional components later:
- Claude subagents: `.claude/agents/`
- Claude hooks: `.claude/hooks/`
- repo tooling (linters, test runners) and environment bootstrap

Keep this incremental: start with skills, add other artifacts only when the core path is stable.

### Supply-chain safety (non-negotiable)
Because skills/plugins can execute code or influence tool use:
- fetch only from an **allowlisted set of repos** (trusted internal registry),
- prefer content review for script-backed skills,
- keep “reader” skills tool-limited (where supported),
- avoid “install from random catalog” as a default workflow.

## Outcome
With a manifest + installer CLI, teams get:
- one repeatable install/update workflow for Codex and Claude,
- batch installation with reproducible versions,
- a clean customization story via overlays,
- a path to add hooks/subagents/env setup later,
- reduced context bloat (store large docs/specs in `references/`, not in `SKILL.md` bodies).

