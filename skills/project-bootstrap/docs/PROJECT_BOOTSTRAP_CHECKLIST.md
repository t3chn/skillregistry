---
title: "Project Bootstrap Checklist (Manual)"
status: active
---

# Project Bootstrap Checklist (manual, universal)

## 0) Decide scope
- [ ] Repo type: **single** or **monorepo**
- [ ] If monorepo: list subprojects (e.g. `web/`, `mobile/`, `backend/`, `shared/`)
- [ ] Define standard commands per (sub)project: `fmt`, `lint`, `test`, `build`, `run`

## 1) Beads (mandatory from the start)
- [ ] `bd onboard` → `bd ready`
- [ ] Create starter issues: `bootstrap`, `prek`, `ci`, `dev-env`, `docs`
- [ ] Monorepo: split work by area (choose a convention and stick to it)
  - [ ] Option A (recommended): create one epic per area (`web`, `mobile`, `backend`, `shared`) and add child tasks via `--parent`
  - [ ] Option B: keep tasks flat, but enforce title prefixes (`web:`, `mobile:`, `backend:`) + labels (`web`, `mobile`, `backend`, `shared`)
  - [ ] Option C (advanced): separate backlogs via rigs (only if you truly need isolated workflows)
- [ ] Monorepo: define cross-cutting buckets (`shared`, `infra`, `ci`, `docs`) and use `bd dep` for cross-area blockers
- [ ] `bd sync` after meaningful progress

## 2) Prek (mandatory from the start)
- [ ] `uvx prek --version`
- [ ] Create `.pre-commit-config.yaml`:
  - [ ] Single repo: root only
  - [ ] Monorepo (workspace mode): root **plus** one in each subproject dir
- [ ] Monorepo: set `orphan: true` in each subproject config (avoid double-processing by parents)
- [ ] Add `.prekignore` (and/or `.gitignore`) for heavy dirs (`node_modules/`, `dist/`, `build/`, `.venv/`, `Pods/`, etc.)
- [ ] `uvx prek validate-config`
- [ ] `uvx prek install` (run from workspace root)
- [ ] `uvx prek run --all-files`
- [ ] Monorepo targeting: `uvx prek run web/ --all-files` (same for `backend/`, `mobile/`)

## 3) Repo basics
- [ ] `README.md` with quickstart + the standard commands
- [ ] `.env.example` (if env vars/secrets are used)
- [ ] Ignore build artifacts (git + prekignore)

## 4) CI (minimum)
- [ ] Run `uvx prek run --all-files`
- [ ] Run tests (and separate lint if not covered by prek)
- [ ] Monorepo: path-filters per subproject (`web/**`, `backend/**`, `mobile/**`)

## 5) Optional: agent/skills bootstrap
- [ ] Install baseline + language skills from your trusted registry
- [ ] Create/update `project-workflow` overlay (wired to `fmt/lint/test/build/run`)
- [ ] Review `.agent/skills_todo.md`

## 6) End-of-session
- [ ] All green locally (prek + tests)
- [ ] `bd sync`
- [ ] `git pull --rebase` → `git push` → `git status` clean/up-to-date
