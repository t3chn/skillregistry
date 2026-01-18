---
name: api-{{API_NAME}}
description: Project API integration notes for {{API_NAME}}. Use when implementing or debugging {{API_NAME}} calls.
---

# API: {{API_NAME}}

## What we know (fill this)
- Base URL: TODO
- Auth: TODO (API key? OAuth? JWT?)
- Rate limits: TODO
- Idempotency rules: TODO
- Retries/timeouts: TODO

## Endpoints (fill this)
- TODO list main endpoints used by this project.

## Error handling checklist
- Always log request id / correlation id if provided.
- Distinguish retryable vs non-retryable errors.
- Add timeouts and backoff.

## References
- See `references/TODO.md`
- Add OpenAPI/Swagger spec into `references/` if available.
