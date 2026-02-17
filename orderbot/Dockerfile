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

# Run the FastMCP server
CMD ["uv", "run", "app/main.py"]