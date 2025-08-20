#!/bin/bash

docker buildx build --push \
  --platform linux/amd64,linux/arm64 \
  --tag uitadmin/criaparse:latest.6-beta \
  --tag uitadmin/criaparse:v0.3.4.6-beta .