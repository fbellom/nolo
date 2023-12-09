# Makefile for building and managing a Docker container

# Image name
IMAGE_NAME := noloreader/proxy

# Image tag
IMAGE_TAG := latest

# Docker registry (if pushing to a registry)
DOCKER_REGISTRY := 536422989755.dkr.ecr.us-east-1.amazonaws.com

# Full image name
FULL_IMAGE_NAME := $(DOCKER_REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)

# Default target
.PHONY: all
all: build

# Build the Docker image
.PHONY: build
build:
	docker build -t $(IMAGE_NAME):$(IMAGE_TAG) .

# Tag the Docker image
.PHONY: tag
tag:
	docker tag $(IMAGE_NAME):$(IMAGE_TAG) $(FULL_IMAGE_NAME)

# Push the Docker image
.PHONY: push
push: tag
	docker push $(FULL_IMAGE_NAME)

# Remove the Docker image
.PHONY: clean
clean:
	docker rmi $(IMAGE_NAME):$(IMAGE_TAG)
	docker rmi $(FULL_IMAGE_NAME)