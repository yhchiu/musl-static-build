# Development

[中文](zh-TW/development.md) · [Add a program](adding-a-target.md)

## Tests

```bash
python3 -B -m unittest discover -s tests -v
```

The suite needs Python 3. It simulates Docker and does not use the network. It covers the CLI, adding a target without changing the runner, a failed version lookup, cleanup when extracting a binary fails, and rejection of a dynamically linked artifact.

When `./dist/<target>/` already contains that target's binaries, the same command checks them. Run it from the directory that contains `dist/`. A missing binary skips that target. These checks do not start a Docker build.

Version comparison runs only when `dist/<target>/VERSION` exists. The binary must report that version. Without the file, the comparison is skipped. `build-static.sh` writes the file and then runs the matching checks.

| Target | What the optional check covers |
|--------|--------------------------------|
| Apache | Static link, the compiled-in module lists for event and prefork, APR and APR-util versions from this build, `htpasswd`, and one local HTTP response from each server. The HTTP responses run as `nobody` and need root. |
| curl | Static link, and HTTPS plus HTTP/2 in `--version`. |
| wget | Static link, and HTTPS, zlib, and PCRE2 in `--version`. |
| rsync | Static link, `--version`, and one local file copy. |
| OpenSSL | Static link, `version`, and one self-signed certificate. |
| Git | Every exported binary is static. `--version`, `--exec-path` for an absolute path, and one local commit. |
| OpenSSH | Every binary for that release is static. `ssh -V` decides whether `sshd-session` and `sshd-auth` must be present. |
| PHP | `php-cli`, `php-cgi`, and `php-fpm` are static and report the same `x.y.z` release. `php -m` includes the extensions selected by this target. One local FastCGI response checks `php-fpm`. As root, that response runs the worker as `nobody` and needs that account. |
| nginx | Static link, version/build options, HTTP, proxy, rewrite, auth subrequests, status, gzip/static gzip, Brotli, TLS 1.2/1.3 and HTTP/2 ALPN/SETTINGS. PHP-FPM integration also runs when `dist/php/php-fpm` exists. HTTP/3 is compiled in but not handshake-tested. |
| stunnel | Static link/version, TLS 1.2/1.3 server forwarding, verified TLS client forwarding and rejection of a wrong hostname or untrusted certificate. |

The nginx and stunnel TLS checks need an `openssl` command to generate temporary certificates; they skip those checks if it is absent. Service checks use ephemeral loopback ports, temporary configs and bounded process cleanup. They do not need Internet access.

Compiling a newly added target still needs a real Docker build before that version is listed as checked.

## Layout

```text
musl-static-build/
├── build-static.sh          # locates the project and loads lib/build.sh
├── lib/
│   └── build.sh             # CLI, discovery, validation, Docker, export
├── targets/
│   ├── php/
│   ├── openssh/
│   ├── curl/
│   ├── wget/
│   ├── rsync/
│   ├── openssl/
│   ├── git/
│   ├── apache/
│   ├── nginx/
│   └── stunnel/             # each has target.sh and Dockerfile
├── tests/                   # unittest suite; runtime checks are optional
├── docs/                    # guides linked from the README
├── README.md
├── README.zh-TW.md
└── dist/                    # build output, gitignored, next to your shell's cwd
```

The runner loads the selected module, validates and resolves its version, then appends static-link checks and `/out` exports to its Dockerfile. It builds the image, copies the declared binaries, and removes the temporary container. Copying a binary out of the container removes that container on failure as well. Every exported binary is checked, including PHP CLI, CGI, and FPM.

## Change a target's build

Feature selection and compiler flags live in the target's build files. The CLI accepts a target, a version, `--clean`, and `--no-test`. `targets/<name>/target.sh` holds the version, the Alpine tag, and the exported filenames.

| Change | File |
|--------|------|
| `./configure`, `LDFLAGS`, and `make` for most targets | `targets/<name>/Dockerfile` |
| Git make variables | `targets/git/build.sh`. The Dockerfile in that directory also builds a small static libcurl for Git |
| Apache MPMs, modules, and `CFLAGS` | `targets/apache/build-mpms.sh`. APR and APR-util flags are in `targets/apache/Dockerfile` |

The next build reads `targets/<name>/Dockerfile`. The runner rewrites `dist/<target>/Dockerfile` from that file and appends the static-link checks. Edits under `dist/` are replaced on the next build.

Docker rebuilds from the first changed `RUN`. It does the same when a copied script changes (`targets/git/build.sh` or `targets/apache/build-mpms.sh`). Pass `--clean` to ignore the Docker cache for the whole build.

Published tests and the "Checked" notes on each target page cover the default build. A modified binary still has to be reported as `statically linked`, or the build stops. Its feature set is outside what this project supports. Apache and nginx keep `-fno-pie` / `-no-pie` so that check can pass. This nginx build does not use `-march=native`, so the binary is not tied to the build machine's instruction set.
