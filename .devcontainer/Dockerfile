FROM python:3.12-bullseye

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock* /tmp/

# Install dependencies with uv
RUN cd /tmp && uv pip install --system -r pyproject.toml