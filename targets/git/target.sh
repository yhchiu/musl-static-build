#!/bin/bash

TARGET_DESCRIPTION="git"
DEFAULT_VERSION="2.56.0"
VERSION_PATTERN='^2\.[0-9]+\.[0-9]+$'
VERSION_HELP="2.x.y (exact release)"
ALPINE_VERSION="3.20"
# Helpers sit next to git. Shell scripts are not exported.
ARTIFACTS=(
    "git:git"
    "git-receive-pack:git-receive-pack"
    "git-upload-pack:git-upload-pack"
    "git-upload-archive:git-upload-archive"
    "git-shell:git-shell"
    "git-http-backend:git-http-backend"
    "git-remote-http:git-remote-http"
    "git-remote-https:git-remote-https"
)
