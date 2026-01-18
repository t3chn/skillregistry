---
name: lang-rust
description: Rust conventions and reliability checklist for agents using cargo, clippy, and tests.
---

# Rust Conventions

- Use `cargo fmt` and `cargo clippy` where available.
- Prefer explicit error types and context; avoid `unwrap()` in production code.
- Keep changes compiling at each step; run `cargo test`.
- Be mindful of lifetimes/ownership; keep APIs simple.
