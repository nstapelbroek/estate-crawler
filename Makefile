IMAGE=nstapelbroek/estate-crawler
BUILD=docker build --target
RUN=docker run --rm -it
STRUCTURE_TEST_FILE=dev/docker/structure-tests.yaml

verify: lint validate check

lint:
	cat Dockerfile | docker run --rm -i hadolint/hadolint hadolint --ignore SC2035 --ignore DL3018 -

check:
	$(BUILD) Check -t $(IMAGE) .

.prod-build:
	$(BUILD) Prod -t $(IMAGE) .

prod: .prod-build
	$(RUN) $(IMAGE)

validate: .prod-build
	$(RUN) -v /var/run/docker.sock:/var/run/docker.sock -v $(CURDIR)/$(STRUCTURE_TEST_FILE):/tmp/tests.yaml gcr.io/gcp-runtimes/container-structure-test test --image $(IMAGE) --config /tmp/tests.yaml

validate-pr:
	$(BUILD) Prod -t $(IMAGE) --cache-from nstapelbroek/estate-crawler:latest .
	$(RUN) -v /var/run/docker.sock:/var/run/docker.sock -v $(CURDIR)/$(STRUCTURE_TEST_FILE):/tmp/tests.yaml gcr.io/gcp-runtimes/container-structure-test test --image $(IMAGE) --config /tmp/tests.yaml

dive: .prod-build
	$(RUN) -v //var/run/docker.sock:/var/run/docker.sock wagoodman/dive $(IMAGE)

.PHONY: verify lint check prod .prod-build validate validate-pr dive
