---
title: "One Skill Registry, Two Delivery Channels: Codex Repo Skills vs Claude Marketplace Plugins"
date: 2026-01
tags: [skills, codex-cli, claude-code, delivery, submodule, symlink, marketplace, plugins, supply-chain]
status: draft
open_questions:
  - "Add primary sources for Codex skill discovery locations + precedence rules."
  - "Add primary sources for Claude plugin marketplace commands and copy/symlink behavior."
---

# One Skill Registry, Two Delivery Channels: Codex Repo Skills vs Claude Marketplace Plugins

## Premise
Assume a **trusted internal skill registry**: one or more Git repositories in your org (GitHub/GitLab/self-hosted). This provides governance (review, tags, signing, CI) and avoids dependency on third-party catalogs.

From that single source of truth, deliver skills to two runtimes in two “native” ways:
- **Codex CLI**: repo-scoped skill folders (simple, deterministic, Git-native).
- **Claude Code**: marketplace-installed **plugins** (skills + hooks + agents + commands + MCP/LSP), with update ergonomics.

## Codex CLI: best-practice delivery for team projects

### Default: repo-scoped skills
Prefer installing skills into the repository under `.codex/skills/` so the whole team shares the same baseline.

### Option A (recommended): git submodule + symlinks into `.codex/skills/`
Mechanics:
- Add the registry as a submodule pinned to a commit, e.g. `.vendor/skillregistry`.
- Symlink only the needed skill folders into `.codex/skills/`.

Example:
```
.vendor/skillregistry  (git submodule @ pinned commit)
.codex/skills/lang-go  -> ../../.vendor/skillregistry/skills/lang-go
.codex/skills/tdd-loop -> ../../.vendor/skillregistry/skills/tdd-loop
```

Pros:
- deterministic versions via pinned submodule commit,
- projects include only selected skills (no “global junk drawer”),
- updates are trivial: bump submodule pointer and restart Codex.

Cons:
- symlinks can be painful on some Windows setups; if needed, replace symlinks with a sync/copy step.

### Option B: Codex `skill-installer` for quick experiments
Codex includes a system skill (`skill-installer`) that can install skills from GitHub paths into the user skill directory.

Use case:
- rapid local experimentation (user-scoped installs),
- quick “try this skill” flows.

Limitations for team/project delivery:
- tends to be user-local rather than repo-native,
- updating often becomes “reinstall/replace” unless you build extra conventions.

## Claude Code: best-practice delivery via Marketplace Plugins

### Two delivery modes exist
1) repo-scoped skills in `.claude/skills/` (simple, but skills-only),
2) marketplace plugins (recommended for “batteries included”: skills + hooks + subagents + commands).

### Why plugins are a better “delivery unit” for Claude
Plugins can bundle:
- multiple skills,
- hooks (guardrails, logging),
- agents/subagents,
- commands and tool integrations,
- MCP/LSP servers (where applicable).

Marketplaces also provide:
- centralized discovery within the org,
- version tracking,
- update workflows (and sometimes auto-update UX).

### Packaging constraint
Marketplace installs commonly **copy** plugin directories into a cache. Avoid plugins that reference files outside their own directory via `../...`, because those won’t be carried along. If sharing files is required, keep them inside the plugin directory (or ensure symlink semantics are compatible with the copier).

## Organizing the registry for “select only what you need”

### For Codex: unit of distribution = skill folder
Registry layout:
```
skillregistry/
  skills/
    lang-go/
    lang-rust/
    testing-tdd-loop/
    api-openapi-generic/
    project-bootstrap/
```
Keep large artifacts out of `SKILL.md`; store them in `references/` and use scripts for selective extraction.

### For Claude: unit of distribution = plugin
Use a dedicated marketplace repo that groups skills into installable sets:
```
skillregistry-claude-marketplace/
  .claude-plugin/marketplace.json
  plugins/
    dev-core/
      .claude-plugin/plugin.json
      skills/...
      hooks/...
      agents/...
      commands/...
    go-stack/
      ...
    rust-stack/
      ...
```
Suggested “atoms”:
- `dev-core` (bootstrap, review, tdd loop, logging hooks),
- `go-stack` / `rust-stack` (language-specific add-ons),
- `api-<vendor>` (integration-specific bundles when needed).

## Updates without a “universal installer”

### Codex: updates via Git
- bump submodule commit → restart Codex.

### Claude: updates via marketplace
- update marketplace index → update plugins (optionally auto-update), then restart if required by the runtime UX.

## Customization without breaking updates
Two robust patterns:

### Pattern 1 (preferred): config-driven skills
Keep shared skills generic; store project specifics in project-owned config files (e.g., `.agent/project_profile.yaml`, workflow docs). The skill instructs: “read the project config and follow it.”

### Pattern 2: override by precedence
When a hard override is required, create a project-scoped skill with the same `name` to override a plugin/global skill (depending on the runtime’s precedence rules). Use sparingly; prefer Pattern 1.

## Minimal MVP (Jan 2026)
1) A trusted internal `skillregistry` repo with `skills/` folders.
2) Codex projects consume via submodule + `.codex/skills` symlinks (or sync copy).
3) Claude consumes via an org marketplace repo with 2–5 plugins (`dev-core`, `go-stack`, etc.).
4) Optional: repo onboarding config so teammates get prompted to install trusted marketplace plugins when they open/trust the repo.

## Security notes (non-optional)
Treat skills/plugins as supply-chain code:
- use allowlisted repos only,
- review script-backed skills,
- constrain tool permissions (where supported),
- avoid “install from random catalog” workflows for team projects.

