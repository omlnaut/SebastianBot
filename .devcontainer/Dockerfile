FROM python:3.12-bullseye

# Install Node.js (required for Pi)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs

# Install Pi global
RUN npm install -g @earendil-works/pi-coding-agent

# Install Poetry
RUN pip install poetry

COPY pyproject.toml poetry.lock /tmp/

# Install dependencies with Poetry
RUN cd /tmp && poetry config virtualenvs.create false && poetry install
