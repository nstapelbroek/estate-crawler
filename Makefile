.PHONY: build run publish

# Variables
MAKEPATH := $(abspath $(lastword $(MAKEFILE_LIST)))
PWD := $(dir $(MAKEPATH))
PROJECTNAME=docker.io/nstapelbroek/estate-crawler
TAGNAME=latest

build:
	docker build --tag $(PROJECTNAME):$(TAGNAME) --pull .

publish:
	docker push $(PROJECTNAME):$(TAGNAME)
