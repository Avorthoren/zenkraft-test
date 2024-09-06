# 'make main' to build Dockerfile.main.
# 'make' / 'make all' to build all containers. There is only one currently.

.DEFAULT_GOAL := all

GIT_VERSION := $(shell git describe --abbrev=7 --dirty --always --tags)

define compile
	$(eval DOCKERTAG:= 'zenkraft-test-$(1):latest')
	echo $(GIT_VERSION) > VERSION
	docker build -t $(DOCKERTAG) -f Dockerfile.$(1) .
endef

main:
	$(call compile,main)

all: main

.PHONY: all main
