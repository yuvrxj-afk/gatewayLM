from locust import HttpUser, task, between

TEAM_KEY = "gw-alpha-dev-key-1234"

class GatewayUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task
    def chat_ping(self):
        # Use local Ollama / mock models to avoid spending API credits.
        with self.client.post(
            "/v1/chat",
            headers={"x-api-key": TEAM_KEY},
            json={
                "model": "granite3.3:2b",
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 16,
                "temperature": 0,
            },
            name="/v1/chat",
            catch_response=True,
        ) as r:
            # 429s are expected under rate limiting; don't count them as failures.
            if r.status_code in (200, 429):
                r.success()
            else:
                r.failure(f"{r.status_code}: {r.text[:200]}")
