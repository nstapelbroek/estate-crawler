FROM python:3.7-alpine

RUN apk add -U --no-cache libxml2-dev libffi-dev gcc build-base libxslt-dev zlib-dev libffi-dev libssl1.0 openssl-dev python3-dev ca-certificates

RUN pip install pipenv setuptools

COPY . /app

WORKDIR /app

RUN pipenv install --system --deploy

ENTRYPOINT ["python", "crawler.py"]
CMD ["--region", "amsterdam"]