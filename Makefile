.PHONY: build init run

# Variables
MAKEPATH := $(abspath $(lastword $(MAKEFILE_LIST)))
PWD := $(dir $(MAKEPATH))
PROJECTNAME=nstapelbroek/estate-crawler

init:
	pip install -r requirements.txt

build:
	docker build --tag $(PROJECTNAME) --file $(PWD)/dev/docker/Dockerfile .

run:
	python ./crawler.py
