FROM public.ecr.aws/lambda/python:3.9

WORKDIR /var/task

# Copy only lockfiles first so Docker can cache the layer if unchanged
COPY pyproject.toml poetry.lock ./

# Install Poetry
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir poetry
# Configure Poetry so it doesn't use a separate virtualenv
RUN poetry config virtualenvs.create false
# Now install deps (which go to global Python site-packages)
RUN poetry install --without dev --no-interaction --no-ansi --no-root && poetry run pip list

# copy actual code (app/, infra/, etc.)
COPY . .

CMD ["app.main.handler"]
