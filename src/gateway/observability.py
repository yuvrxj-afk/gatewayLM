"""
Observability — Prometheus metrics + OpenTelemetry tracing.

Metrics exposed at GET /metrics (scraped by Prometheus every 15s).
Traces emitted via OpenTelemetry SDK (stdout exporter for now).
"""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from prometheus_client import Counter, Histogram, Gauge

# ── OpenTelemetry setup ────────────────────────────────────────────────────────

provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(provider)

tracer = trace.get_tracer("gateway")

# ── Prometheus metrics ─────────────────────────────────────────────────────────

requests_total = Counter(
    "gateway_requests_total",
    "Total requests handled",
    ["team", "model", "provider", "status"],
)

request_latency = Histogram(
    "gateway_request_latency_seconds",
    "End-to-end request latency",
    ["team", "model", "provider"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

tokens_total = Counter(
    "gateway_tokens_total",
    "Total tokens processed",
    ["team", "model", "provider", "type"],  # type = input | output
)

cost_total = Counter(
    "gateway_cost_usd_total",
    "Total spend in USD",
    ["team", "model"],
)

rate_limit_hits = Counter(
    "gateway_rate_limit_hits_total",
    "Requests rejected by rate limiter",
    ["team", "limit_type"],  # limit_type = rpm | tpm
)

budget_hits = Counter(
    "gateway_budget_cap_hits_total",
    "Requests rejected by budget cap",
    ["team"],
)

circuit_breaker_state = Gauge(
    "gateway_circuit_breaker_open",
    "1 if circuit breaker is open for this provider",
    ["provider"],
)

fallback_events = Counter(
    "gateway_fallback_events_total",
    "Times a fallback provider was used",
    ["from_provider", "to_provider"],
)
