#!/bin/bash
# Shared CLI and Docker lifecycle. Target-specific code lives in targets/.

fail() {
    echo "Error: $*" >&2
    exit 1
}

target_names() {
    local config name
    for config in "$PROJECT_ROOT"/targets/*/target.sh; do
        [ -f "$config" ] || continue
        name="${config%/target.sh}"
        name="${name##*/}"
        [[ "$name" =~ ^[a-z][a-z0-9_-]*$ ]] || continue
        printf '%s\n' "$name"
    done
}

target_exists() {
    [[ "$1" =~ ^[a-z][a-z0-9_-]*$ ]] &&
        [ -f "$PROJECT_ROOT/targets/$1/target.sh" ]
}

# Print the missing tool names, or nothing when both python3 and pytest exist.
# pytest may be a command or a module importable by python3.
missing_runtime_tools() {
    local missing=""
    if ! command -v python3 >/dev/null 2>&1; then
        missing="python3"
    fi
    if ! command -v pytest >/dev/null 2>&1; then
        if [ -n "$missing" ] || ! python3 -c 'import pytest' >/dev/null 2>&1; then
            if [ -n "$missing" ]; then
                missing="$missing and pytest"
            else
                missing="pytest"
            fi
        fi
    fi
    printf '%s\n' "$missing"
}

list_targets() {
    local name
    while IFS= read -r name; do
        (
            source "$PROJECT_ROOT/targets/$name/target.sh"
            printf '  %-12s %-24s default: %s; versions: %s\n' \
                "$name" "$TARGET_DESCRIPTION" "$DEFAULT_VERSION" "$VERSION_HELP"
        )
    done < <(target_names)
}

usage() {
    cat <<'USAGE'
Usage:
  ./build-static.sh <target> [version] [--clean] [--no-test]
  ./build-static.sh --list

Targets:
USAGE
    list_targets
    cat <<'USAGE'

Examples:
  ./build-static.sh                  # show help
  ./build-static.sh php              # build latest PHP 8.5.x
  ./build-static.sh php 8.4          # build latest PHP 8.4.x
  ./build-static.sh php 8.5.11       # build a specific PHP release
  ./build-static.sh php --clean      # rebuild PHP without Docker cache
  ./build-static.sh openssh          # build OpenSSH 9.9p2
  ./build-static.sh openssh 8.9p1
  ./build-static.sh openssh 9.3p1 --clean

Notes:
  - A build requires a target
  - No arguments, -h, --help, help, or any arguments without a target display this help
  - --clean passes --no-cache to Docker and may appear anywhere
  - --no-test skips artifact checks and may appear anywhere
  - Artifact checks need python3 and pytest; if either is missing, the build skips them and says so
  - A build records its version in dist/<target>/VERSION
  - Every exported binary must be statically linked
USAGE
}

parse_args() {
    TARGET=""
    VERSION=""
    BUILD_OPTIONS=()
    RUN_RUNTIME_TESTS=1
    local arg

    if [ $# -eq 0 ]; then
        usage
        exit 0
    fi
    for arg in "$@"; do
        case "$arg" in
            -h|--help|help) usage; exit 0 ;;
            --list) list_targets; exit 0 ;;
        esac
    done
    for arg in "$@"; do
        if [ "$arg" = "--clean" ]; then
            BUILD_OPTIONS=(--no-cache)
        elif [ "$arg" = "--no-test" ]; then
            RUN_RUNTIME_TESTS=0
        elif target_exists "$arg"; then
            [ -z "$TARGET" ] || fail "specify only one target"
            TARGET="$arg"
        else
            [ -z "$VERSION" ] || fail "unexpected argument: $arg"
            VERSION="$arg"
        fi
    done
    if [ -z "$TARGET" ]; then
        usage
        exit 0
    fi
}

load_target() {
    TARGET_DIR="$PROJECT_ROOT/targets/$TARGET"
    DEFAULT_VERSION=""
    VERSION_PATTERN=""
    TARGET_DESCRIPTION=""
    VERSION_HELP=""
    ALPINE_VERSION="3.20"
    ARTIFACTS=()
    unset -f target_prepare
    source "$TARGET_DIR/target.sh"

    [ -n "$DEFAULT_VERSION" ] && [ -n "$VERSION_PATTERN" ] &&
        [ -n "$TARGET_DESCRIPTION" ] && [ -n "$VERSION_HELP" ] ||
        fail "incomplete target metadata: $TARGET"
    [ -f "$TARGET_DIR/Dockerfile" ] || fail "missing Dockerfile for $TARGET"
    [ "${#ARTIFACTS[@]}" -gt 0 ] || fail "no artifacts declared for $TARGET"

    VERSION="${VERSION:-$DEFAULT_VERSION}"
    [[ "$VERSION" =~ $VERSION_PATTERN ]] ||
        fail "invalid $TARGET version '$VERSION'; expected $VERSION_HELP"

    # Artifact paths are inserted into shell commands in the Dockerfile.
    local artifact source destination seen=" "
    for artifact in "${ARTIFACTS[@]}"; do
        [[ "$artifact" == *:* ]] || fail "invalid artifact mapping: $artifact"
        source="${artifact%%:*}"
        destination="${artifact#*:}"
        [[ "$source" =~ ^[a-zA-Z0-9_][a-zA-Z0-9_./-]*$ ]] &&
            [[ "/$source/" != *'/../'* ]] &&
            [[ "$destination" =~ ^[a-zA-Z0-9_][a-zA-Z0-9_.-]*$ ]] ||
            fail "invalid artifact mapping: $artifact"
        [[ "$seen" != *" $destination "* ]] || fail "duplicate artifact: $destination"
        seen+="$destination "
    done
}

write_dockerfile() {
    cat "$TARGET_DIR/Dockerfile"
    printf '\n# Shared verification and export of every declared artifact.\n'
    printf 'RUN mkdir -p /out'
    local artifact source destination
    for artifact in "${ARTIFACTS[@]}"; do
        source="${artifact%%:*}"
        destination="${artifact#*:}"
        printf ' && %s\n' '\'
        printf "    file '%s' | grep -q 'statically linked'" "$source"
        printf ' && %s\n' '\'
        printf "    cp '%s' '/out/%s'" "$source" "$destination"
    done
    printf '\n'
}

build_target() (
    # A subshell scopes cleanup traps to this build.
    local output_dir="$(pwd)/dist/$TARGET"
    local image="$TARGET-static-builder"
    local container_id="" artifact destination
    cleanup() {
        if [ -n "$container_id" ]; then
            docker rm "$container_id" >/dev/null || true
        fi
    }
    trap cleanup EXIT
    trap 'exit 130' INT
    trap 'exit 143' TERM

    if declare -F target_prepare >/dev/null; then
        target_prepare
    fi

    echo "[progress] Build $TARGET_DESCRIPTION $VERSION (Alpine $ALPINE_VERSION)..."
    mkdir -p "$output_dir"
    write_dockerfile > "$output_dir/Dockerfile"
    docker build "${BUILD_OPTIONS[@]}" \
        --build-arg "VERSION=$VERSION" \
        --build-arg "ALPINE_VERSION=$ALPINE_VERSION" \
        -t "$image" -f "$output_dir/Dockerfile" "$TARGET_DIR"

    echo "[progress] Extract $TARGET_DESCRIPTION binaries..."
    container_id=$(docker create "$image")
    for artifact in "${ARTIFACTS[@]}"; do
        destination="${artifact#*:}"
        docker cp "$container_id:/out/$destination" "$output_dir/$destination"
    done
    docker rm "$container_id" >/dev/null
    container_id=""
    printf '%s\n' "$VERSION" > "$output_dir/VERSION"
    local runtime_file="$PROJECT_ROOT/tests/test_${TARGET}_runtime.py"
    if [ -f "$runtime_file" ] && [ "$RUN_RUNTIME_TESTS" -ne 1 ]; then
        echo "[progress] Artifact checks were not run (--no-test)"
    elif [ -f "$runtime_file" ]; then
        local missing runtime_dist
        missing="$(missing_runtime_tools)"
        if [ -n "$missing" ]; then
            echo "[progress] Artifact checks were not run: ${missing} not found"
        else
            echo "[progress] Check $TARGET_DESCRIPTION $VERSION..."
            runtime_dist="$(cd -- "$(dirname -- "$output_dir")" && pwd)"
            (
                cd -- "$PROJECT_ROOT"
                RUNTIME_DIST="$runtime_dist" python3 -B -m unittest discover \
                    -s tests -p "test_${TARGET}_runtime.py"
            )
        fi
    fi
    echo "$TARGET_DESCRIPTION $VERSION static build OK: $output_dir"
)

main() {
    parse_args "$@"
    load_target
    build_target
}
