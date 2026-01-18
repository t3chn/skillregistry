---
title: "Fully Autonomous Development Pipelines (Ralph Loop): Approaches and Stages"
date: 2026-01
tags: [agents, orchestration, ralph-loop, workflow, planning, verification, code-review]
notes:
  - "This is a structured English rewrite of a Russian research note."
---

# Fully Autonomous Development Pipelines (Ralph Loop): Approaches and Stages

## Overview: what Ralph Loop is and why it matters
Ralph Loop is an approach to autonomous software development with AI agents, named after Ralph Wiggum from *The Simpsons* to emphasize persistence. The agent runs in a loop: it receives a goal, performs development steps, and repeats iterations until the task is **actually** complete. The practical promise is simple: “leave the agent running overnight and wake up to a working result”.

The idea was popularized via Claude Code (Anthropic) and quickly spread to other agentic tools (OpenAI Codex CLI, Cursor, Copilot-like CLIs, and custom wrappers). The ambition is an end-to-end pipeline: requirements → code → tests → fixes → release readiness, with minimal human intervention.

In practice, fully autonomous loops only work reliably when they follow a clear staged structure, strong quality checks, and explicit “stop” criteria. This document summarizes a stable pipeline shape that shows up across multiple implementations and community practices.

## The core stages of an autonomous Ralph-style pipeline
Below is a common stage breakdown. Different tools name these stages differently, but the functional sequence is similar.

### 1) Brainstorming & goal setting
Define the work at a product/feature level:
- for new features/MVP: requirements, user stories, and acceptance criteria
- for refactors: scope and the measurable improvement target (performance, migration, modernization)

Key success factor: a concrete **Definition of Done** (DoD). Avoid vague goals (“make it good”). Prefer checkable outcomes (“CRUD API with validation; tests >80%; prints COMPLETE only when all checks pass”).

Automation is often limited here: humans usually provide the initial scope, sometimes using AI to expand ideas.

### 2) Discovery & clarification
Before planning, the agent needs context:
- in existing repos: codebase/documentation survey, environment understanding
- for ambiguous work: ask clarifying questions (requirements, constraints, edge cases)

A common community pattern is an explicit “interview phase”: the agent must ask questions before planning. Some tool ecosystems formalize a planner/executor split (“planner plans, Ralph executes”).

Exit criteria: no major unknowns remain; the agent has read the key files and has enough context to produce a plan.

### 3) Planning
Produce a detailed plan before coding:
- architecture decisions and rationale
- files/modules to create or modify
- step sequence with verification per step
- rollback/safety strategy (especially for risky changes)

Community experience: planning quality dominates outcomes. A wrong plan can lead to fast, confident wrong implementation; spending 2–3× more time on the plan often pays back during execution.

Common practice: cross-review the plan with a second model/agent before building.

Exit criteria: plan is stable, reviewed, and accepted (by a human and/or by cross-model review).

### 4) Task decomposition (explicit task list)
Convert the plan into an explicit checklist the loop can execute:
- Markdown checkboxes, or
- JSON with `passes: false/true`, per user story/task

Example structure (conceptual):
- a list of tasks, each with acceptance criteria and a completion flag

Why it matters: it bounds scope, enables progress tracking, and gives the loop a deterministic “next step”.

Exit criteria: task list exists, tasks are small enough to fit in an iteration, and each has objective acceptance criteria.

### 5) Iterative development loop (the “Ralph” core)
A typical iteration does:
1. Select the next unfinished task (highest priority `passes: false`).
2. Re-load authoritative context (plan + task list + progress log).
3. Implement code changes for the selected task.
4. Run checks (tests/build/lint/typecheck).
5. If checks fail: fix and re-run until green.
6. Update task state (`passes: true`) and append to progress.
7. Commit changes (often one commit per completed task).
8. Decide whether to continue or finish (based on global DoD).

This can be orchestrated with a simple loop wrapper (e.g., `while true; do ...; done`) and a completion token such as `<promise>COMPLETE</promise>` that halts the wrapper.

Exit criteria: the chosen task is done and validated; the loop moves to the next task. Global stop happens only when all tasks are done and final checks pass.

### 6) Testing & verification (as a first-class gate)
Testing is not “at the end”. It’s a gate on every step:
- unit/integration tests
- compilation/type checking
- linters/static analyzers
- repo-specific “completion predicates” (e.g., “no Jest imports remain”, “vitest config exists”, etc.)

Some systems implement a `verifyCompletion` function to programmatically check repository state, not just test output.

Exit criteria: all required checks are green and completion predicates are satisfied.

### 7) Review & reflection
After the loop says “done”, add a review phase before merging:
- cross-model review (different model reviews the diff and returns `SHIP`/`FIX`)
- optional “safe refactor loop” to improve code quality while keeping tests green
- human review is still recommended, especially for architecture and security
- optionally, external review tools (additional AI reviewers) as an extra filter

Also include “plan vs fact” reconciliation: update the plan/spec with what was actually built and why.

Exit criteria: no critical review findings remain; documentation is updated to reflect the actual implementation.

### 8) Refactor & optimize (optional or separate loop)
If the primary goal is refactoring, the pipeline is the same, but tasks are “behavior-preserving” and tests are the main guardrail. Some teams run refactoring as a separate post-feature loop to avoid scope creep.

Exit criteria: quality improvements delivered with no regressions (tests green, lint/format green).

### 9) Completion & release readiness
The loop emits a completion token and stops. Depending on trust level, the pipeline may:
- produce a PR,
- prepare a merge-ready branch,
- update docs/README/changelog,
- optionally clean up temporary logs/artifacts (or move them into docs).

Always apply resource safety: max iterations, timeouts, budgets, and “stuck” escape hatches.

## Stage transitions and exit criteria (recommended)
- **Discovery → Plan**: all critical unknowns resolved; key files read; constraints clear.
- **Plan → Build**: plan reviewed/approved (human or cross-model); task list generated.
- **Within Dev Loop**: each task requires green checks before marking complete.
- **Stop Condition**: all tasks complete + final verification passes + explicit completion token emitted.
- **Safety Stops**: `--max-iterations`, time budget, cost budget; on exhaustion, stop and report what’s stuck.

## Tooling patterns (Claude Code, Codex CLI, and general wrappers)
### Claude Code (Anthropic)
Commonly cited capabilities:
- explicit loop plugin (`/ralph-loop`) with max iterations and completion promise
- planning mode (`/plan`) that writes a plan without modifying code
- ecosystem plugins that separate roles (planner vs executor), e.g., “Lisa plans, Ralph does”

### OpenAI Codex CLI
Commonly cited capabilities/patterns:
- `/init` to create `AGENTS.md` with build/test/lint/run rules (persistent repo guidance)
- different command approval / access modes (read-only → auto/apply → full access)
- `/review` as an internal review step
- “plan mode” often emulated via prompts and saving `PLAN.md` manually (if no dedicated command)

### General wrappers and custom orchestrators
Teams frequently build wrappers that:
- manage task lists (Markdown/JSON) and priorities
- run multiple agents via separate branches/worktrees (advanced)
- track iteration metrics, budgets, and failure patterns

## Multi-language support: “quality gates” per ecosystem
The loop structure is language-agnostic, but verification is language-specific:
- Python: `pytest`, optional `mypy`/`ruff`/`flake8`
- JS/TS: `npm|pnpm|yarn` scripts, `tsc`, test runner, framework configs
- Go: `go test ./...`, `go test` + `gofmt`/lint gates
- Rust: `cargo test`, `cargo check`, `cargo clippy`

For polyglot repos, define multi-language gates and treat “task done” as “all relevant gates pass”.

## What tends to work vs. what fails (community patterns)
### Works well
- Explicit, checkable DoD (tests, predicates, checklists).
- Small iterations with strong feedback loops (tests every step).
- Progress artifacts + commits (append-only progress log; one commit per task).
- Cross-model role separation (planner vs builder vs reviewer).
- HITL early, AFK later (train the pipeline before letting it run unattended).
- Stuck detection and limits (escape hatches, iteration/time/cost caps).

### Common failure patterns
- Vague objectives (“make it better”) → endless loops or premature “done”.
- No quality gates → unbounded bugs and unsafe code.
- Rigid plan-following despite new info → divergence from the real goal.
- Over-assigning subjective/creative work without objective tests.
- No logging/observability → hard to debug why the loop stalled.

## Reference table: the 9-step pipeline at a glance
| Stage | Purpose | Typical automation / notes |
|---|---|---|
| Brainstorm | Define scope + DoD | Mostly human + light AI help |
| Discovery | Read repo, ask questions | Tool file-reading, explicit Q&A |
| Plan | Detailed implementation plan | Dedicated plan mode or prompt-driven plan file |
| Decompose | Convert plan → tasks | Markdown checkboxes or JSON `passes` |
| Dev loop | Implement tasks iteratively | Code + checks + commit per task |
| Test | Continuous verification | Tests/build/lint/typecheck each iteration |
| Review | Quality gate before merge | Cross-model review + human review |
| Refactor | Improve maintainability | Separate “safe refactor loop” with tests green |
| Release | Stop + handoff | Completion token, PR/branch, docs updates |

## Key takeaway
Fully autonomous development loops are viable when the pipeline is engineered like a production system: crisp objectives, explicit task state, continuous verification, strong observability, and resource limits. When those ingredients are missing, the loop predictably drifts, thrashes, or “declares victory” too early. The operator’s job shifts from writing every line of code to designing the pipeline: defining DoD, shaping tasks, setting gates, and reviewing outputs.

