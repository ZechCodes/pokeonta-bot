FROM python:3.8-slim-buster
MAINTAINER Zech Zimmerman "hi@zech.codes"

WORKDIR /usr/src/app

COPY --from=ghcr.io/astral-sh/uv:0.13.4 /uv /bin/uv
COPY scripts/refresh_ca_trust.py scripts/refresh_ca_trust.py
RUN uv pip install --system "certifi==2026.10.19" "poetry==1.8.5" && \
    python scripts/refresh_ca_trust.py
RUN poetry config virtualenvs.in-project true

COPY pyproject.toml .
COPY poetry.lock .
RUN poetry install

RUN mkdir -p /usr/src/app/tmp
ENV TMPDIR /usr/src/app/tmp

COPY ./production.yaml .

COPY ./pokeonta ./pokeonta

CMD ["poetry", "run", "python", "-u", "-m", "pokeonta"]
