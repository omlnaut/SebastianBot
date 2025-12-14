FROM python:3.12-bullseye

# Install Poetry
RUN pip install poetry

COPY pyproject.toml poetry.lock /tmp/

# Install dependencies with Poetry
RUN cd /tmp && poetry config virtualenvs.create false && poetry install