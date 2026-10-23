#!/bin/bash

TARGET_DESCRIPTION="Apache httpd"
DEFAULT_VERSION="2.4.69"
VERSION_PATTERN='^2\.4\.[0-9]+$'
VERSION_HELP="2.4.x (exact release)"
ALPINE_VERSION="3.20"
# Libtool writes the real binaries under .libs/. Those paths cannot be
# artifact sources, so the Dockerfile copies them to static-bin/ first.
ARTIFACTS=(
    "static-bin/httpd:httpd"
    "static-bin/httpd-prefork:httpd-prefork"
    "static-bin/htpasswd:htpasswd"
)
