---
name: project-workflow
description: Project-specific canonical workflow: how to build/test/lint/run and what DONE means.
---

# Project Workflow

## Canonical commands
- Build: `{{BUILD_CMD}}`
- Test: `{{TEST_CMD}}`
- Lint/Format: `{{LINT_CMD}}`
- Run/Dev: `{{RUN_CMD}}`

## Definition of Done (DoD)
- All tests pass.
- Lint/format passes (or is explicitly skipped with a reason).
- No TODO markers left in generated workflow unless explicitly accepted in `.agent/skills_todo.md`.
- Changes are committed with clear message and minimal diff.

