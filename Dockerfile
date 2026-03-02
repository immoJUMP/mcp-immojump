FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    IMMOJUMP_MCP_TRANSPORT=streamable-http \
    IMMOJUMP_MCP_HOST=0.0.0.0 \
    IMMOJUMP_MCP_PORT=8000

WORKDIR /app

COPY pyproject.toml README.md LICENSE /app/
COPY src /app/src

RUN python -m pip install --upgrade pip \
    && python -m pip install .

EXPOSE 8000

CMD ["mcp-immojump"]
