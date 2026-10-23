#!/bin/bash

TARGET_DESCRIPTION="PHP"
DEFAULT_VERSION="8.5"
VERSION_PATTERN='^[0-9]+\.[0-9]+(\.[0-9]+)?$'
VERSION_HELP="x.y (latest patch) or x.y.z (exact release)"
ALPINE_VERSION="3.20"
ARTIFACTS=("sapi/cli/php:php-cli" "sapi/cgi/php-cgi:php-cgi" "sapi/fpm/php-fpm:php-fpm")

target_prepare() {
    if [[ "$VERSION" =~ ^[0-9]+\.[0-9]+$ ]]; then
        local series="$VERSION"
        local release_json resolved_version

        echo "[progress] Resolve latest PHP ${series}.x release..."
        if ! release_json=$(docker run --rm "alpine:$ALPINE_VERSION" wget -qO- \
            "https://www.php.net/releases/index.php?json&version=${series}"); then
            fail "failed to fetch PHP ${series} release information"
        fi
        resolved_version=$(printf '%s\n' "$release_json" | sed -nE \
            's/.*"version"[[:space:]]*:[[:space:]]*"([0-9]+\.[0-9]+\.[0-9]+)".*/\1/p')
        if ! [[ "$resolved_version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || \
            [ "${resolved_version%.*}" != "$series" ]; then
            fail "could not resolve a PHP ${series}.x release"
        fi
        VERSION="$resolved_version"
    fi
}
