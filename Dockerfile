FROM python:3-alpine AS base
RUN apk add --no-cache libxml2-dev libffi-dev gcc build-base libxslt-dev zlib-dev libffi-dev libssl1.0 openssl-dev

ENV PIP_NO_CACHE_DIR=false
RUN pip install pipenv==2018.11.26

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
RUN pipenv check

# The final release
FROM release As Prod
ENTRYPOINT ["python", "crawler.py"]
CMD ["--region", "amsterdam"]