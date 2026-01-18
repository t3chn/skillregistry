---
title: "Pipeline Stage 1: Brainstorming & Goal Setting"
date: 2026-01
tags: [agents, ralph-loop, pipeline, requirements, prd, definition-of-done, yagni, smart-goals]
notes:
  - "Structured English rewrite of a Russian research note."
---

# Pipeline Stage 1: Brainstorming & Goal Setting

## Stage overview
The first stage defines the project’s **vision, goal, and boundaries**.
- For a new MVP/feature: collect requirements and define desired functionality.
- For refactoring: define what should improve (performance, migration, maintainability) and how success will be measured.

The typical output is a rough **PRD** (Product Requirements Document) or a list of **user stories** with **acceptance criteria**. Automation is intentionally limited: humans usually lead scope definition, while AI can help expand ideas and surface missing questions.

The decisive factor for a successful autonomous loop is a crisp **finish line**: a clear, checkable **Definition of Done (DoD)**. Vague goals (“build a good TODO app”) cause thrashing or premature completion. Concrete, testable goals (“CRUD REST API; input validation; >80% test coverage; emit `COMPLETE` only when all requirements pass”) give the loop a stable target and reduce infinite wandering.

## Best practices for brainstorming and goal setting
### Start from product intent, not implementation
Focus on:
- the user and the problem being solved,
- core use cases and non-negotiable requirements,
- constraints (security, compliance, performance, timeline),
- explicit success metrics and failure conditions,
- what is **out of scope** (and why).

Good PRDs force “hard questions” early: who the users are, what value is delivered, how success is measured, and what will *not* be built in this release.

### Use iterative Q&A to reduce blind spots
A practical pattern is a short iterative loop:
1) ask key questions, 2) record answers into the PRD, 3) ask the next question.

Example question set:
- What is the primary goal and target users?
- What must the user be able to do (must-have vs nice-to-have)?
- What constraints exist (platform, security, budget, timeline)?
- How is success measured (metrics, SLAs, coverage targets)?
- What is explicitly out of scope for this release?

Keep the brainstorming phase separate from implementation planning. If the conversation drifts into file structure or step-by-step coding, pause and return to “what/why”.

### Apply YAGNI/KISS aggressively
Especially for MVP work, enforce “minimum necessary scope”:
- trim non-critical features early,
- reduce conceptual surface area,
- prefer fewer, well-defined user stories over broad wishlists.

This minimizes noise and improves convergence later in the loop.

## Should technology choices be included at this stage?
It depends:
- If stack constraints are already decided (e.g., “backend Go, frontend React”), state them as explicit constraints so the PRD is realistic.
- If the stack is not predetermined, avoid premature technical debate. First lock down **what** must be built and **why**; choose **how** (stack/architecture) in the next stage.

A useful compromise is to capture only high-level constraints (e.g., “must run on Linux”, “must support Postgres”) and postpone detailed framework/library selection.

## Why separating “what” vs “how” matters
When the stage is product-focused:
- requirements are clearer and more testable,
- success criteria can be made **SMART** (specific, measurable, achievable, relevant, time-bound),
- architecture choices are driven by goals rather than bias toward familiar tooling.

Mixing early technical detail into ideation often creates noise and derails user-centered thinking.

## Reliability: avoiding omissions and infinite loops
Because this stage can rely heavily on dialogue, introduce explicit self-check mechanisms:

### Use a PRD checklist
Define an “idea completeness” checklist and ensure the PRD covers each item:
- target users and primary job-to-be-done
- core user stories (must-have)
- acceptance criteria / DoD
- constraints (security, performance, legal, platform)
- success metrics
- risks and assumptions
- out of scope

### Run a “coverage review” pass
After drafting the PRD, run a short verification pass:
- “Does the PRD cover every checklist item?”
- “Are any acceptance criteria subjective or untestable?”
- “Are there hidden edge cases that need explicit policy decisions?”

### Limit iterations and use independent review
Do not rely solely on the same model’s self-evaluation. Add:
- iteration limits (to prevent endless refinement),
- a second reviewer (another model or a human) for final sanity checks.

## Outcome
A strong Brainstorming & Goal Setting stage produces a bounded, testable PRD that downstream loops can execute reliably. The clearer the DoD and scope boundaries, the less the autonomous pipeline will drift, thrash, or stop early.
