#!/bin/bash

TARGET_DESCRIPTION="nginx"
DEFAULT_VERSION="1.30.6"
VERSION_PATTERN='^1\.[0-9]+\.[0-9]+$'
VERSION_HELP="1.x.y, from 1.26.0 upward (exact release)"
ALPINE_VERSION="3.20"
ARTIFACTS=("objs/nginx:nginx")

target_prepare() {
    local minor="${VERSION#*.}"
    minor="${minor%%.*}"
    (( 10#$minor >= 26 )) || fail "nginx needs version 1.26.0 or newer for this module set"
}
