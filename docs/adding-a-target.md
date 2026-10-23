# Add a program

[中文](zh-TW/adding-a-target.md) · [Development checks](development.md)

A new program is a directory under `targets/`. The runner discovers it. The CLI and `lib/build.sh` stay unchanged.

```text
targets/<name>/target.sh     # version rules and artifact names
targets/<name>/Dockerfile    # download, configure, and static link
```

`<name>` starts with a lowercase letter and may contain lowercase letters, digits, `_`, or `-`. `./build-static.sh --list` prints the new name after both files exist.

curl and wget are the smallest real modules to copy from.

## target.sh

```bash
TARGET_DESCRIPTION="Example tool"
DEFAULT_VERSION="1.0.0"
VERSION_PATTERN='^[0-9]+\.[0-9]+\.[0-9]+$'
VERSION_HELP="x.y.z"
ALPINE_VERSION="3.20"
ARTIFACTS=("example:example")
```

| Variable | Role |
|----------|------|
| `TARGET_DESCRIPTION` | Name printed in help and progress lines |
| `DEFAULT_VERSION` | Used when the command omits a version |
| `VERSION_PATTERN` | Bash extended regular expression the version must match |
| `VERSION_HELP` | Text shown when the version does not match |
| `ALPINE_VERSION` | Alpine tag passed as the `ALPINE_VERSION` build arg |
| `ARTIFACTS` | `source:output-name` pairs for every binary to export |

`source` is relative to the Dockerfile's final `WORKDIR`. `output-name` is the filename written to `dist/<name>/`. List every binary that should leave the image. The runner checks the mappings, rejects duplicates, and refuses a binary that `file` does not describe as `statically linked`.

Keep the top of `target.sh` limited to assignments and function definitions. Help and target discovery source the file in a subshell. Network requests and other preparation belong in `target_prepare()`.

### target_prepare

This hook is optional. It runs after version validation and before the Dockerfile is written. It may replace `VERSION` or `ALPINE_VERSION`. PHP uses it to turn `8.5` into the current `8.5.x` release. OpenSSH uses it to pick Alpine 3.16 for 8.x and to drop `sshd-session` / `sshd-auth` on releases that do not have those programs.

On failure, call `fail "message"`. That prints `Error: message` and exits.

These modules are trusted project code. The runner does not sandbox them.

## Dockerfile

A tiny file that exercises the interface:

```dockerfile
ARG ALPINE_VERSION=3.20
FROM alpine:${ALPINE_VERSION}
RUN apk add --no-cache build-base file
ARG VERSION
WORKDIR /usr/src/example-${VERSION}
RUN printf '#include <stdio.h>\nint main(void) { puts("example"); return 0; }\n' > example.c && \
    cc -static -Os -o example example.c && strip example
```

For a real program, replace the sample compile with that program's source download, configure step, and static link. The runner passes `VERSION` and `ALPINE_VERSION` as build arguments. The final image must contain `file`, `grep`, `mkdir`, and `cp`. The runner appends a `RUN` that checks each artifact and copies it to `/out`.

The Docker build context is `targets/<name>/`. Put any file the Dockerfile `COPY`s into that directory.

After the module builds for real, record the checked version on the program's doc page and in the README table. The unit tests simulate Docker and do not compile the new program.
