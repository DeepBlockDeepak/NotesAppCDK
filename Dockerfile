FROM public.ecr.aws/lambda/python:3.9

WORKDIR /var/task

COPY pyproject.toml poetry.lock ./

RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir poetry
# configure Poetry so it doesn't use a separate virtualenv
RUN poetry config virtualenvs.create false

COPY . .

# install deps (which go to global Python site-packages)
RUN poetry install --without dev --no-interaction --no-ansi && poetry run pip list

CMD ["src.note_app.main.handler"]
