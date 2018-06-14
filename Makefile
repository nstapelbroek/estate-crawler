.PHONY: build install run publish

# Variables
MAKEPATH := $(abspath $(lastword $(MAKEFILE_LIST)))
PWD := $(dir $(MAKEPATH))
PROJECTNAME=docker.io/nstapelbroek/estate-crawler
TAGNAME=latest

install:
	pip install -r requirements.txt --user

build:
	docker build --tag $(PROJECTNAME):$(TAGNAME) --file $(PWD)dev/docker/Dockerfile --pull .

publish:
	docker push $(PROJECTNAME):$(TAGNAME)

run:
	python ./crawler.py --region amsterdam
