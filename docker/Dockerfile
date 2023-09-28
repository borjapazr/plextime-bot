# syntax=docker/dockerfile:1.6-labs

FROM python:3.11-buster as builder

ENV PYTHONFAULTHANDLER=true \
  PYTHONUNBUFFERED=true \
  PYTHONHASHSEED=random \
  PIP_DEFAULT_TIMEOUT=100 \
  PIP_DISABLE_PIP_VERSION_CHECK=true \
  PIP_NO_CACHE_DIR=true \
  POETRY_VERSION=1.6.1 \
  POETRY_VIRTUALENVS_IN_PROJECT=true \
  POETRY_VIRTUALENVS_CREATE=true

RUN pip install poetry==${POETRY_VERSION}

WORKDIR /bot

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-cache --no-interaction --no-ansi --no-root --only main

COPY plextime_bot ./plextime_bot/
COPY README.md py.typed ./

RUN <<EOF
poetry build --no-cache -f wheel
./.venv/bin/pip install --no-cache-dir --only-binary :all: dist/*.whl
EOF

FROM python:3.11-alpine as runtime

LABEL maintainer="Borja Paz Rodríguez <borjapazr@gmail.com>" \
  version="1.0" \
  description="🤖⏰ Bot for automatic checkin and checkout on Plextime platform" \
  license="MIT" \
  org.label-schema.name="PlextimeBot" \
  org.label-schema.description="🤖⏰ Bot for automatic checkin and checkout on Plextime platform" \
  org.label-schema.url="https://bpaz.dev" \
  org.label-schema.vcs-url="https://github.com/borjapazr/plextime-bot" \
  org.label-schema.version="1.0.0" \
  org.label-schema.schema-version="1.0"

ENV PYTHONFAULTHANDLER=true \
  PYTHONUNBUFFERED=true \
  PYTHONHASHSEED=random \
  VIRTUAL_ENV=/bot/.venv \
  PATH=/bot/.venv/bin:$PATH

WORKDIR /bot

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

CMD ["python", "-m", "plextime_bot"]
