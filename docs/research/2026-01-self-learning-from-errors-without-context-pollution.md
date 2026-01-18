---
title: "Self-Learning from Agent Errors Without Context Pollution"
date: 2026-01
tags: [agents, skills, memory, reflection, guardrails, hooks, evals, ralph-loop]
status: draft
open_questions:
  - "Add primary sources for: context poisoning claims, Skills release timelines, Letta metrics."
---

# Self-Learning from Agent Errors Without Context Pollution

## Problem: session resets vs. context overload
Most current AI coding agents effectively start each new session with limited memory of prior failures. A naive workaround is to paste raw error logs and full transcripts into the next prompt. In practice, this often:
- overwhelms the context window with low-signal noise,
- introduces contradictions and stale details,
- degrades performance (“context poisoning” / “context rot” effects).

The goal is to enable **learning from past mistakes** while keeping the working context **small, relevant, and stable**.

## Core solution: dynamic “Skills” as modular external memory
“Skills” (as used in tools like Codex CLI and Claude Code) are a pragmatic mechanism for persistent knowledge:
- each skill is a small module (typically a folder with `SKILL.md`, optionally scripts/resources),
- skills live **outside** the main chat context,
- the runtime loads skills **on demand** when triggers match the task (progressive disclosure).

This changes the memory model:
- raw logs remain external artifacts (files),
- distilled lessons become structured, reusable rules (skills),
- the agent loads only what it needs, when it needs it.

### Why this avoids context pollution
Instead of injecting a large history blob, the agent:
1) sees a lightweight skill catalog (names + descriptions),
2) chooses a relevant skill based on the current task,
3) reads only that skill’s instructions as needed.

## How skills typically work (high-level model)
While implementations differ, common mechanics look like this:
- the tool scans a skills directory (e.g., `~/.codex/skills`, `~/.claude/skills`, or project-local equivalents),
- each skill exposes metadata (name/description/triggers) in a YAML frontmatter,
- during execution the tool selects skills whose descriptions match the situation,
- the full `SKILL.md` is read only when the tool/model decides it is necessary.

Key property: **progressive disclosure** (load small, then expand).

## A self-learning loop using reflection → skills
A practical “learn without bloating context” pipeline:

### 1) Post-mortem reflection (outside the main working prompt)
Capture structured traces of what went wrong (not everything):
- failing commands + exit codes,
- the last N lines of stderr,
- which files were changed,
- which checks failed (tests/lint/build),
- any repeated failure patterns.

Then run a dedicated retro step (human or model) to extract a short set of lessons:
- what failed, why it failed (best guess),
- the minimal “rule” that would have prevented it,
- what to do next time (checklist, guardrail, or known pitfall).

### 2) Convert lessons into a new or updated skill
Turn the retro into a small, actionable `SKILL.md`:
- narrow scope (“Testing Best Practices”, “Avoid common Cython build pitfalls”, “Git hygiene for this repo”),
- explicit triggers (“pytest”, “tests failed”, “CI red”, “Cython”, “pip install -e”, etc.),
- concise steps and verification commands,
- a “common pitfalls” section for recurring issues.

If a lesson belongs to an existing skill, update that skill rather than creating a new one.

### 3) Install and version the skill
Place the skill where the agent runtime can discover it:
- global: `~/.codex/skills/<skill>/SKILL.md`, `~/.claude/skills/<skill>/SKILL.md`
- project overlay: `.codex/skills/<skill>/SKILL.md`, `.claude/skills/<skill>/SKILL.md` (when supported/desired)

Treat skills as code:
- keep them small,
- version them in git (skill registry),
- review changes like any other operational policy.

### 4) Validate behavior change (regression-style)
Re-run a few representative scenarios:
- confirm the skill triggers when expected,
- confirm it does not trigger in unrelated work,
- confirm it changes behavior (e.g., tests are run earlier, known pitfall is checked proactively).

## Example: preventing a recurring build failure
A common pattern: a task fails repeatedly due to a known ecosystem pitfall. After retro, you create a skill that:
- instructs the agent to search for known problematic patterns (e.g., deprecated types),
- fixes them *before* running the build,
- re-runs the build and tests.

Net effect: the next session follows a proactive checklist and avoids the same failure mode without needing to replay the entire prior transcript.

## Alternatives and complementary approaches
Skills are one tool. Depending on platform constraints, the following can complement or substitute:

### Project “always-loaded” docs (AGENTS.md / CLAUDE.md)
Use project docs for stable, always-relevant rules:
- how to build/test/lint/run,
- repo conventions and constraints,
- security constraints and forbidden patterns.

Keep them short; link out to deeper docs instead of embedding everything.

### Hooks / guardrails (especially in Claude Code)
External hooks can enforce non-negotiable conditions without spending model tokens:
- “don’t allow completion if tests are failing”,
- log failures after each tool invocation,
- auto-run checks on session end.

Hooks act as a runtime policy layer rather than memory, and pair well with skills (hooks capture data; skills encode lessons).

### A “critic” subagent for retros
A separate agent/context can:
- analyze full transcripts and logs deeply,
- produce a compact retro summary,
- propose skill updates without polluting the main working context.

### Episodic memory approaches (research lineage)
Patterns like Reflexion-style lessons, MemGPT-like memory tiers, or Zettelkasten-like note systems aim to:
- store short “lessons learned” externally,
- retrieve only relevant ones per task.

They require careful retrieval design to avoid pulling irrelevant memories.

### In-session refinement (Self-Refine / tool-assisted critique)
Not cross-session learning, but reduces mistakes per session:
- draft → critique → revise loops,
- tool-based verification (run tests, compile, lint) integrated into the agent’s routine.

### Policy/prompt optimization + evals
For repeated workloads, treat agent behavior as a configuration problem:
- adjust prompts/policies based on failures,
- add regression evals that reproduce past failure scenarios,
- ensure improvements do not introduce new regressions.

## Practical implementation guidance
### 1) Scaffold “starter” skills at project kickoff
Create minimal project-specific skills early (e.g., `project-workflow`, `api-<name>`), so the agent starts with correct commands and constraints.

### 2) Reuse from a trusted skill registry
Prefer importing a curated set of skills from a trusted registry rather than ad-hoc copying from the internet. Install only what’s needed to avoid trigger noise.

### 3) Use a skill generator to reduce manual effort
If your agent environment includes a “skill creator” capability, use it to bootstrap the structure, then edit for precision and scope.

### 4) Log failures externally, then summarize
A robust pattern is:
- collect structured error events into a file (e.g., `.agent/session_errors.jsonl`),
- run a retro summarizer that outputs `.agent/retro.md`,
- generate/update skills from the retro summary (not from raw logs).

Minimal pseudo-logger for tool failures:
```python
# post_tool_use_logger.py (pseudocode)
event = read_json_stdin()
if event.tool == "bash" and event.exit_code != 0:
    append_jsonl(".agent/session_errors.jsonl", {
        "cmd": event.command,
        "exit_code": event.exit_code,
        "stderr_tail": tail(event.stderr, 500),
    })
```

### 5) Keep skills clean and precise
Rules of thumb:
- narrow trigger conditions (avoid “always on” skills),
- keep skills short and local (one concern per skill),
- prefer checklists and commands over long explanations,
- avoid embedding large logs/specs; put those in `references/` and link to them.

## Key takeaway
To “learn without context bloat”, treat experience as a pipeline:
**raw traces → compact retro → reusable skill (policy) → regression verification**.
This preserves the benefits of fresh-context loops while steadily improving agent behavior across sessions.

