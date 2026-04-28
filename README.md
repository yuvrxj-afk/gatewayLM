# GatewayLM — LLM API Gateway (Prod-grade)

GatewayLM is a production-style API gateway that sits in front of LLM providers and enforces **team auth**, **rate limits**, **token budgets**, **fallback routing**, and **observability**.

## What This Is

- **One endpoint** for all teams: `POST /v1/chat`
- **Team-scoped policy enforcement**: API keys → team config → allowlists, limits, budgets
- **Resilience**: retries, fallback chains, circuit breaker
- **Observability**: `/metrics` for Prometheus + Grafana dashboards; OpenTelemetry spans

## Quickstart (Local)

### 1) Install deps

```bash
uv sync --dev
```

### 2) Configure environment

```bash
cp .env.example .env
```

Required:
- `REDIS_URL`

Optional:
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`
- `OLLAMA_BASE_URL` (defaults to `http://localhost:11434`)

### 3) Start infra + gateway (Docker)

```bash
docker compose up --build
```

Then open:
- Grafana: `http://localhost:3000` (user/pass: `admin` / `admin`)
- Prometheus: `http://localhost:9090`

### 4) Call the gateway

```bash
curl -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -H "x-api-key: gw-alpha-dev-key-1234" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Say pong."}]
  }'
```

## Local Ollama (No API credits)

If you run Ollama on your Mac, the gateway container can reach it via:

- `OLLAMA_BASE_URL=http://host.docker.internal:11434`

Example model from this repo’s setup:
- `granite3.3:2b`

```bash
curl -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -H "x-api-key: gw-alpha-dev-key-1234" \
  -d '{
    "model": "granite3.3:2b",
    "messages": [{"role": "user", "content": "Say pong."}]
  }'
```

## Request lifecycle (high level)

`/v1/chat`:
1. **Auth**: `x-api-key` → Team config
2. **RPM limiter**: Redis token bucket (requests/min)
3. **Call provider**: router selects provider (with fallback + circuit breaker)
4. **TPM limiter**: tokens/min counter (post-response)
5. **Budget**: compute cost from token usage → monthly cap enforcement
6. **Metrics**: counters + latency histograms

## Testing

Run integration tests (no paid APIs required):

```bash
APP_ENV=test .venv/bin/pytest tests/ -v
```

### Mock providers (offline)

Start mock providers (OpenAI/Anthropic/Ollama compatible stubs):

```bash
docker compose up -d mock-providers
```

Then run tests with provider base URLs pointed at mocks:

```bash
APP_ENV=test \
OPENAI_BASE_URL=http://localhost:9000 \
ANTHROPIC_BASE_URL=http://localhost:9000 \
OLLAMA_BASE_URL=http://localhost:9000 \
.venv/bin/pytest tests/ -v
```

## Load testing (safe, no credits)

```bash
locust -f loadtest/locustfile.py --host http://localhost:8000
```

Use small concurrency for local Ollama (start at 10–50 users). 429s are treated as expected.

## What This Is Not

- Not an “LLM app” (no chains/agents)
- Not tied to one provider
- Not a demo-only prototype — design is intentionally production-leaning
