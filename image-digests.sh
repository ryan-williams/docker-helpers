#!/usr/bin/env bash

docker inspect "$@" | jq '.[0]|{Id,RepoTags,RepoDigests,Created}'
