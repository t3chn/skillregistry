---
name: lang-python
description: Python conventions and reliability checklist for agents (tests, formatting, typing where appropriate).
---

# Python Conventions

- Prefer `pyproject.toml`-driven tooling when present.
- Keep functions small and testable; add tests for edge cases.
- Run `pytest` (or the project’s test command) before declaring done.
- Use a formatter/linter if configured (e.g., ruff/black).
