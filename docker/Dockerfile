FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml ./
RUN pip install uv && UV_SYSTEM_PYTHON=1 uv sync --no-dev
COPY src/ ./src/
COPY config/ ./config/
EXPOSE 8000
CMD ["uvicorn", "src.gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
