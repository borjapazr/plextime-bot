ARG PYTHON_VERSION=3.11
ARG POETRY_VERSION=1.6.1

FROM python:${PYTHON_VERSION}-buster AS builder

ARG POETRY_VERSION

ENV PYTHONFAULTHANDLER=true \
  PYTHONUNBUFFERED=true \
  PYTHONHASHSEED=random \
  PIP_DEFAULT_TIMEOUT=100 \
  PIP_DISABLE_PIP_VERSION_CHECK=true \
  PIP_NO_CACHE_DIR=true \
  POETRY_VIRTUALENVS_IN_PROJECT=true \
  POETRY_VIRTUALENVS_CREATE=true

RUN pip install poetry==${POETRY_VERSION}

WORKDIR /bot

COPY --link pyproject.toml poetry.lock ./

RUN poetry install --no-cache --no-interaction --no-ansi --no-root --only main

COPY --link plextime_bot ./plextime_bot/
COPY --link README.md py.typed ./

RUN poetry build --no-cache -f wheel && \
  ./.venv/bin/pip install --no-cache-dir --only-binary :all: dist/*.whl

FROM python:${PYTHON_VERSION}-alpine AS runtime

LABEL maintainer="Borja Paz Rodríguez <borjapazr@gmail.com>" \
  version="1.2.0" \
  description="🤖⏰ Bot for automatic check-in and check-out on Plextime platform" \
  license="MIT" \
  org.label-schema.name="PlextimeBot" \
  org.label-schema.description="🤖⏰ Bot for automatic check-in and check-out on Plextime platform" \
  org.label-schema.url="https://bpaz.dev" \
  org.label-schema.vcs-url="https://github.com/borjapazr/plextime-bot" \
  org.label-schema.version="1.2.0" \
  org.label-schema.schema-version="1.0"

ENV PYTHONFAULTHANDLER=true \
  PYTHONUNBUFFERED=true \
  PYTHONHASHSEED=random \
  VIRTUAL_ENV=/bot/.venv \
  PATH=/bot/.venv/bin:$PATH

WORKDIR /bot

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

VOLUME ["/bot/logs"]

HEALTHCHECK --start-period=20s --interval=30s --timeout=3s --retries=5 CMD pgrep -f plextime_bot > /dev/null || exit 1

CMD ["python", "-m", "plextime_bot"]
