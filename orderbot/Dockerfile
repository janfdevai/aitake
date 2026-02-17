# Use a slim Python image
FROM python:3.12-slim

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY . .

# Install dependencies
RUN uv sync

# Expose the port (Cloud Run sets this dynamically)
EXPOSE 8080
CMD ["uv", "run", "fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8080"]