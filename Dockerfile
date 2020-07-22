FROM python:3.7-alpine3.8 AS base
RUN apk add --no-cache libxml2-dev libffi-dev gcc build-base libxslt-dev zlib-dev libffi-dev openssl-dev

ENV PIP_NO_CACHE_DIR=off
RUN pip install --upgrade pip && python -m pip install https://github.com/pypa/pipenv/archive/7745e51a63cbd17c7ba9ef9f75ec974f8b5543d1.tar.gz

WORKDIR /app
COPY Pipfile /app/
COPY Pipfile.lock /app/

RUN pipenv install --system --deploy

# App is for base images that do not need dev-dependencies
FROM base AS app
COPY . /app/

# test-base is for images that need dev-dependencies
FROM app AS test-base
RUN pipenv install --system --deploy --dev

# release will form a base for shippable images that are meant to run the application
FROM app AS release
VOLUME buid

# Check is a "public" stage ensuring that language dependencies are safe
FROM test-base AS Check
RUN safety check
RUN pipenv check --system

# CodeStyle is a "public" stage that checks the codestyle of the application
FROM test-base AS CodeStyle
RUN black ./ --line-length 120 --check --diff

# The final release
FROM release As Prod
ENTRYPOINT ["python", "crawler.py"]
CMD ["--region", "amsterdam"]