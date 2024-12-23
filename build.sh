#!/bin/bash

docker buildx build --push \
  --platform linux/amd64,linux/arm64 \
  --tag uitadmin/criaparse:latest \
  --tag uitadmin/criaparse:v0.2.9 .