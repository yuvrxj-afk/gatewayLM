#!/usr/bin/env bash
set -euo pipefail

GATEWAY_URL="${GATEWAY_URL:-http://localhost:8000}"
TEAM_KEY="${TEAM_KEY:-gw-alpha-dev-key-1234}"
MODEL="${MODEL:-granite3.3:2b}" # local Ollama model recommended

say() {
  printf "\n==> %s\n" "$1"
}

req() {
  # usage: req <curl args...>
  curl -sS "$@"
}

http_code() {
  # usage: http_code <curl args...>
  curl -sS -o /dev/null -w "%{http_code}" "$@"
}

say "GatewayLM demo"
echo "Gateway URL:  ${GATEWAY_URL}"
echo "Team key:     ${TEAM_KEY}"
echo "Model:        ${MODEL}"

say "1) Health check"
req "${GATEWAY_URL}/health" | jq -r . 2>/dev/null || req "${GATEWAY_URL}/health"

say "2) Auth enforcement (wrong key -> 401)"
code="$(http_code -X POST "${GATEWAY_URL}/v1/chat" \
  -H "Content-Type: application/json" \
  -H "x-api-key: wrong-key" \
  -d "{\"model\":\"${MODEL}\",\"messages\":[{\"role\":\"user\",\"content\":\"ping\"}]}")"
echo "HTTP ${code}"

say "3) Successful chat through gateway (local Ollama path, no credits)"
req -X POST "${GATEWAY_URL}/v1/chat" \
  -H "Content-Type: application/json" \
  -H "x-api-key: ${TEAM_KEY}" \
  -d "{\"model\":\"${MODEL}\",\"messages\":[{\"role\":\"user\",\"content\":\"Say pong.\"}]}" | jq -r . 2>/dev/null || true

say "4) Rate limit burst (shows 200/429 mix depending on your team limits)"
for i in {1..15}; do
  code="$(http_code -X POST "${GATEWAY_URL}/v1/chat" \
    -H "Content-Type: application/json" \
    -H "x-api-key: ${TEAM_KEY}" \
    -d "{\"model\":\"${MODEL}\",\"messages\":[{\"role\":\"user\",\"content\":\"ping\"}]}")"
  echo "request ${i}: HTTP ${code}"
done

say "5) Metrics endpoint (Prometheus scrape format)"
req "${GATEWAY_URL}/metrics" | head -40
echo "..."

say "6) Admin status (teams)"
req "${GATEWAY_URL}/admin/teams" | jq -r . 2>/dev/null || req "${GATEWAY_URL}/admin/teams"

say "7) Next clicks (optional)"
echo "Grafana:     http://localhost:3000  (admin/admin)"
echo "Prometheus:  http://localhost:9090/targets"
echo "FastAPI docs:${GATEWAY_URL}/docs"

say "Done"

