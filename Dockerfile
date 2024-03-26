FROM python:3.12-alpine3.19 AS base
RUN apk add --no-cache libxml2-dev libffi-dev gcc build-base libxslt-dev zlib-dev libffi-dev openssl-dev

ENV PIP_NO_CACHE_DIR=off
RUN pip install --upgrade pip && python -m pip install pipenv

WORKDIR /app
COPY Pipfile /app/
COPY Pipfile.lock /app/

RUN pipenv install --system --deploy

FROM base AS dev
RUN pipenv install --system --deploy --dev
COPY . /app/

FROM dev AS lint
RUN black ./ --line-length 120 --check --diff

FROM base As release
COPY . /app/
ENTRYPOINT ["python", "crawler.py"]
CMD ["--region", "amsterdam"]