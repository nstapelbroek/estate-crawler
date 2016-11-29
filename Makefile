.PHONY: build init test

# Variables
MAKEPATH := $(abspath $(lastword $(MAKEFILE_LIST)))
PWD := $(dir $(MAKEPATH))
PROJECTNAME=nstapelbroek/estate-crawler

init:
	pip install -r requirements.txt

test:
	nosetests tests

build:
	sudo docker build --tag $(PROJECTNAME) --file ./dev/docker/Dockerfile .

run:
	python ./crawler.py
