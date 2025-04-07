FROM python:3.9-slim

WORKDIR /app

# Copy only lockfiles first so Docker can cache the layer if unchanged
COPY pyproject.toml poetry.lock /app/

# Install Poetry and dependencies
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir poetry
RUN poetry install --without dev --no-interaction --no-ansi --no-root

# copy actual code (app/, infra/, etc.)
COPY . /app

CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
