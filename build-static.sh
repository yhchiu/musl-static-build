#!/bin/bash
# Build static binaries using the modules in targets/<name>/.
set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$PROJECT_ROOT/lib/build.sh"
main "$@"
