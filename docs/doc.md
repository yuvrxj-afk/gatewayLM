# GatewayLM — Build Tracker

> One commit per ticket. Update status as you go.

---

## What We're Building

A production API gateway that sits in front of all your organization's LLM calls. It enforces per-team rate limits and budgets, automatically falls back to alternative providers on outages, and gives you unified observability across every LLM interaction.

**Why this matters:** Every company with more than one team using LLMs ends up building this. It's pure infrastructure engineering applied to AI.

---

## Tech Stack

| Component | Tool | Why |
|-----------|------|-----|
| Language | Python 3.11+ | Strong LLM ecosystem |
| Proxy | FastAPI | Async-native, like Express but typed |
| Rate Limiting | Redis + token bucket | Distributed, sub-ms enforcement |
| Config | YAML + hot reload | No-deploy policy changes |
| Observability | OpenTelemetry + Prometheus | Industry standard |
| Dashboard | Grafana | Unified metrics |
| Providers | OpenAI, Anthropic, Ollama | Multi-provider |
| Containers | Docker + docker-compose | Full stack orchestration |

---

## Phases & Tickets

### Phase 0 — Foundation
> Get the skeleton running before any feature code.

| Ticket | Description | Status |
|--------|-------------|--------|
| P0-T1 | Repo structure, pyproject.toml, FastAPI `/health` endpoint | ✅ done |
| P0-T2 | Dockerfile + Docker Compose (gateway + Redis) | ✅ done |
| P0-T3 | Settings loader — env vars via pydantic-settings | ✅ done |
| P0-T4 | Config loader — `teams.yaml` → typed Pydantic models | ✅ done |

---

### Phase 1 — Proxy Layer
> Translate requests between the gateway's format and each provider's format.

| Ticket | Description | Status |
|--------|-------------|--------|
| P1-T1 | Canonical request/response schema (Pydantic models) | ✅ done |
| P1-T2 | OpenAI provider adapter | ✅ done |
| P1-T3 | Anthropic provider adapter | ✅ done |
| P1-T4 | Ollama provider adapter | ✅ done |
| P1-T5 | Router — pick provider, call it, return unified response | ✅ done |
| P1-T6 | Wire chat router into FastAPI app | ✅ done |
| P1-T7 | Request enrichment (inject system prompts per team config) | ✅ done |

---

### Phase 2 — Auth + Rate Limiting
> Who are you, and are you allowed to do this?

| Ticket | Description | Status |
|--------|-------------|--------|
| P2-T1 | API key auth middleware (validate key → resolve team) | 🔲 todo |
| P2-T2 | Token bucket in Redis — requests per minute | 🔲 todo |
| P2-T3 | Token bucket — tokens per minute (LLM token counting) | 🔲 todo |
| P2-T4 | Budget tracking — cost per request → daily/monthly cap | 🔲 todo |
| P2-T5 | Budget warning at 80%, hard block at 100% | 🔲 todo |
| P2-T6 | Priority tiers — batch vs real-time requests | 🔲 todo |
| P2-T7 | Admin API — view limits, adjust limits, view spending | 🔲 todo |

---

### Phase 3 — Fallback + Resilience
> What happens when a provider falls over?

| Ticket | Description | Status |
|--------|-------------|--------|
| P3-T1 | Provider health checker (background task, every 30s) | 🔲 todo |
| P3-T2 | Fallback chain config (GPT-4o fails → Claude Sonnet) | 🔲 todo |
| P3-T3 | Retry with exponential backoff | 🔲 todo |
| P3-T4 | Distinguish retryable vs non-retryable errors | 🔲 todo |
| P3-T5 | Circuit breaker (open / half-open / closed states) | 🔲 todo |
| P3-T6 | Circuit breaker state persistence in Redis | 🔲 todo |

---

### Phase 4 — Observability
> See everything.

| Ticket | Description | Status |
|--------|-------------|--------|
| P4-T1 | OpenTelemetry setup + spans on every request stage | 🔲 todo |
| P4-T2 | Prometheus metrics export (`/metrics` endpoint) | 🔲 todo |
| P4-T3 | Grafana dashboards (operations, business, performance) | 🔲 todo |
| P4-T4 | Slack alerting rules | 🔲 todo |

---

### Phase 5 — Testing + Load
> Prove it works under pressure.

| Ticket | Description | Status |
|--------|-------------|--------|
| P5-T1 | Integration test suite (pytest) | 🔲 todo |
| P5-T2 | Load test with Locust | 🔲 todo |
| P5-T3 | Mock provider endpoints for offline testing | 🔲 todo |
| P5-T4 | Full Docker Compose with all services wired up | 🔲 todo |

---

### Phase 6 — Polish
> Make it presentable.

| Ticket | Description | Status |
|--------|-------------|--------|
| P6-T1 | Final README | 🔲 todo |
| P6-T2 | `.env.example`, setup script, demo teams | 🔲 todo |
| P6-T3 | Demo recording | 🔲 todo |

---

## Commit Convention

One commit per ticket. Message format:

```
[P{phase}-T{ticket}] short description

e.g.
[P0-T1] repo structure, pyproject.toml, health endpoint
[P1-T2] OpenAI provider adapter
```
