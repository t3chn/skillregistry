---
name: lang-ts
description: TypeScript/JavaScript conventions and reliability checklist for agents (build, typecheck, tests).
---

# TypeScript / JavaScript Conventions

- Prefer the project’s package manager lockfile (`pnpm`/`yarn`/`npm`).
- Run `npm|pnpm|yarn` scripts for build/test/lint; keep CI green.
- If TypeScript is present, ensure `tsc` (or equivalent) passes.
- Avoid introducing new deps unless necessary; document why.
