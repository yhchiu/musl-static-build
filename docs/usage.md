# Build and check

[中文](zh-TW/usage.md) · [Back to the README](../README.md)

`build-static.sh` builds one program at a time. It validates the version, builds an Alpine image, copies the static binaries out, and then checks them.

## Command

```text
./build-static.sh <target> [version] [--clean] [--no-test]
./build-static.sh --list
```

With no arguments, or with `-h`, `--help`, or `help`, the script prints help and does not build.

| Argument | Meaning |
|----------|---------|
| `target` | `php`, `openssh`, `curl`, `wget`, `rsync`, `openssl`, `git`, `apache`, `nginx`, or `stunnel`. `--list` prints the targets the script discovers. |
| `version` | Optional. Each target accepts the forms below. Omit it to use that target's default. |
| `--clean` | Pass `--no-cache` to `docker build`. It may appear anywhere in the command. |
| `--no-test` | Skip the artifact checks after a successful build. It may appear anywhere in the command. |

Give one target and at most one version. A command with no target prints help and does not build, including `./build-static.sh 8.5`, `./build-static.sh 10.6p1`, `./build-static.sh --clean`, and `./build-static.sh --no-test`.

## Version forms

| Target | Form | Example |
|--------|------|---------|
| PHP | `x.y` for the latest patch in that series, or `x.y.z` for one release | `8.5`, `8.5.11` |
| OpenSSH | `8.xpN`, `9.xpN`, or `10.xpN` | `8.9p1`, `9.9p2`, `10.6p1` |
| curl | `8.x.y` | `8.22.0` |
| wget | `1.x.y` | `1.25.0` |
| rsync | `3.x.y` | `3.5.1` |
| OpenSSL | `3.x.y` | `3.5.9` |
| Git | `2.x.y` | `2.56.0` |
| Apache httpd | `2.4.x` | `2.4.69` |
| nginx | `1.x.y`, from 1.26.0 upward | `1.30.6` |
| stunnel | `5.x` | `5.82` |

A PHP `x.y` value is resolved before the compile. The script runs `wget` in an Alpine container and reads the [PHP releases API](https://www.php.net/releases/index.php?json&version=8.5). Use `x.y.z` when you want that exact tarball.

## Where the files go

The script writes to `dist/<target>/` in the **current working directory**, not next to the script. You can start `build-static.sh` from another directory. These files appear after a successful build:

| File | Contents |
|------|----------|
| `dist/<target>/<binary>` | Each static binary that target declares |
| `dist/<target>/VERSION` | The version that was actually built |
| `dist/<target>/Dockerfile` | The target Dockerfile plus the shared static-link checks |

`dist/` is gitignored. The Docker image tag is `<target>-static-builder`. The build context is `targets/<target>/`.

### Build provenance

Each build pulls the selected Alpine tag, resolves its registry digest, and
pins that digest for the Docker build. This refreshes the base image without
turning off the layer cache; `--clean` still forces `--no-cache`.

The output directory also contains:

- `BUILD-INFO.txt`: build time, target/version, Git revision (if available),
  base-image tag, digest and platform, and cache mode.
- `APK-PACKAGES.txt`: Alpine packages actually installed in the builder image.
- `SHA256SUMS`: hashes of the declared binary artifacts. Verify with
  `cd dist/<target> && sha256sum -c SHA256SUMS`.

Note: pinning the Alpine base image **does not pin `apk` repositories**;
packages downloaded during the build can still change. These records support
traceability but do not guarantee a reproducible build or absence of CVEs.
A failed rebuild clears the earlier metadata, but does not remove earlier
binaries from the output directory.

## Checks after the build

A successful build writes `VERSION`, then runs that target's artifact checks. The checks compare the version the binary reports with the version file.

The checks need `python3` and `pytest` on `PATH`. `pytest` may instead be a module that `python3` can import. When either one is missing, the build still succeeds, the version file is still written, and the script prints `Artifact checks were not run`. `--no-test` skips the checks the same way and still writes the version file.

To inspect a binary yourself:

```bash
file dist/php/php-cli dist/php/php-cgi dist/php/php-fpm
file dist/openssh/ssh dist/openssh/sshd
ldd dist/openssh/sshd          # expect: not a dynamic executable
./dist/openssh/ssh -V

file dist/curl/curl
./dist/curl/curl --version

file dist/wget/wget
./dist/wget/wget --version

file dist/rsync/rsync
./dist/rsync/rsync --version

file dist/openssl/openssl
./dist/openssl/openssl version

file dist/git/git
./dist/git/git --version
./dist/git/git --exec-path

file dist/apache/httpd dist/apache/httpd-prefork dist/apache/htpasswd
ldd dist/apache/httpd          # expect: not a dynamic executable
./dist/apache/httpd -v
./dist/apache/httpd -l

file dist/nginx/nginx dist/stunnel/stunnel
./dist/nginx/nginx -V
./dist/stunnel/stunnel -version
```

An HTTPS download also confirms that curl or wget can read the CA store on this machine:

```bash
./dist/curl/curl --fail --location https://curl.se/ -o /dev/null
./dist/wget/wget -O /dev/null https://ftp.gnu.org/gnu/wget/
```

Putting the same files on an older host is covered in [Run on an old host](running-on-old-hosts.md).
