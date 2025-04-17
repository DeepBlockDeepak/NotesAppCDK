FROM public.ecr.aws/lambda/python:3.9

WORKDIR /var/task

COPY pyproject.toml poetry.lock ./

RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir poetry
# configure Poetry so it doesn't use a separate virtualenv
RUN poetry config virtualenvs.create false
# install deps (which go to global Python site-packages)
RUN poetry install --without dev --no-interaction --no-ansi --no-root && poetry run pip list

COPY . .

CMD ["src.note_app.main.handler"]
