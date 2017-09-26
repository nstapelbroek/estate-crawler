.PHONY: build install run

# Variables
MAKEPATH := $(abspath $(lastword $(MAKEFILE_LIST)))
PWD := $(dir $(MAKEPATH))
PROJECTNAME=docker.io/nstapelbroek/estate-crawler

install:
	pip install -r requirements.txt

build:
	docker build --tag $(PROJECTNAME) --file $(PWD)/dev/docker/Dockerfile --pull .

run:
	python ./crawler.py
