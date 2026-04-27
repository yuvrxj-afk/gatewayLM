# GatewayLM — Agent & Contributor Context

> Read this before touching any code. This is the source of truth for how this project is built and why.

---

## What This Is

A production-grade LLM API gateway. Teams inside an organization send their LLM requests here instead of calling OpenAI/Anthropic directly. The gateway handles:

- Auth (API key → team identity)
- Rate limiting (requests/min, tokens/min per team)
- Budget enforcement (monthly spend caps per team)
- Provider routing + fallback (OpenAI → Anthropic if primary is down)
- Circuit breaking (stop hammering a dead provider)
- Observability (traces, metrics, dashboards)

**The caller never knows which provider served the request.**

---

## What This Is Not

- Not an LLM application. No prompts, no chains, no agents.
- Not a managed service wrapper. We own the infra.
- Not a prototype. Every layer is built for production.

---

## Architecture

```
Client Request
    │
    ▼
[Auth Middleware]         → validate API key → resolve team config
    │
    ▼
[Rate Limit Middleware]   → check Redis token bucket → 429 if exceeded
    │
    ▼
[Budget Middleware]       → check team spend → 402 if over cap
    │
    ▼
[Router]                  → select provider via fallback chain
    │
    ▼
[Provider Adapter]        → translate to provider format → call API
    │
    ▼
[Response Normalizer]     → translate back to canonical schema
    │
    ▼
[Observability Layer]     → emit spans + metrics
    │
    ▼
Client Response
```

---

## Tech Stack & Why

| Component | Choice | Reason |
|-----------|--------|--------|
| Language | Python 3.11 | Best LLM ecosystem support |
| Framework | FastAPI | Async-native, typed, auto-docs |
| Validation | Pydantic v2 | Runtime type safety (like Zod) |
| HTTP client | httpx | Async, same API as requests |
| Rate limiting | Redis + token bucket | Distributed, atomic, sub-ms |
| Config | YAML + pydantic-settings | Hot-reloadable, typed |
| Observability | OpenTelemetry + Prometheus | Industry standard |
| Dashboards | Grafana | Unified metrics visualization |
| Package mgmt | uv | Fast, lock-file based (like pnpm) |
| Containers | Docker + Compose | Full stack orchestration |

---

## Code Conventions

**File layout**
```
src/gateway/
  config/       settings.py (env vars), loader.py (YAML)
  models/       schemas.py (canonical request/response types)
  providers/    one file per provider: openai.py, anthropic.py, ollama.py
  middleware/   auth.py, rate_limit.py, budget.py
  routers/      chat.py, admin.py, health.py
  main.py       FastAPI app, middleware registration, startup
```

**Python conventions**
- Type annotations on every function signature — no bare `def foo(x)`
- Pydantic models for all data that crosses a boundary (in/out of functions, in/out of Redis)
- `async def` for all route handlers and anything that does I/O
- No bare `except:` — always catch specific exceptions
- Errors bubble up as FastAPI `HTTPException` with meaningful status codes

**Naming**
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Pydantic models end in their purpose: `ChatRequest`, `ChatResponse`, `GatewayConfig`

---

## Ticket System

Phases and tickets live in `docs/doc.md`. One commit per ticket.

Commit format:
```
[P{phase}-T{ticket}] short description

e.g. [P1-T2] OpenAI provider adapter
```

Current phase: **Phase 1 — Proxy Layer**

---

## Build Philosophy

- **Understand before you write.** Every file we write, we know why it exists.
- **No magic.** If a line of code isn't understood, we don't ship it.
- **Separation of concerns is strict.** Providers don't know about rate limits. Middleware doesn't know about providers.
- **Test the seams.** Unit test individual adapters. Integration test the full request path.
- **Config over code.** Team limits, fallback chains, model allowlists — all in YAML, not hardcoded.

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `config/teams.yaml` | Team definitions, rate limits, budgets, fallback chains |
| `src/gateway/models/schemas.py` | Canonical `ChatRequest` / `ChatResponse` types |
| `src/gateway/config/settings.py` | Env var config (API keys, Redis URL, etc.) |
| `src/gateway/config/loader.py` | YAML → typed Pydantic models |
| `src/gateway/main.py` | FastAPI app entry point |
| `docs/doc.md` | Build tracker — phases, tickets, statuses |
| `docker-compose.yml` | Local stack (gateway + Redis) |
| `.env.example` | All required env vars documented |
