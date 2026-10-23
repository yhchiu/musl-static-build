ARG ALPINE_VERSION=3.20
FROM alpine:${ALPINE_VERSION} AS builder

# musl toolchain + static OpenSSL/zlib
RUN apk update && apk add --no-cache \
    build-base linux-headers musl-dev autoconf automake file wget \
    openssl-dev openssl-libs-static \
    zlib-dev zlib-static

WORKDIR /usr/src

# Download OpenSSH portable source (8.x / 9.x / 10.x)
ARG VERSION
RUN wget https://cdn.openbsd.org/pub/OpenBSD/OpenSSH/portable/openssh-${VERSION}.tar.gz && \
    tar -zxvf openssh-${VERSION}.tar.gz

WORKDIR /usr/src/openssh-${VERSION}

# Static client and server configure:
# - --with-ldflags/-cflags=-static: fully static musl binary
# - --libexecdir: sshd runs sshd-session, sshd-auth, and sftp-server from here
# - disable PAM/SELinux/Kerberos/libedit to avoid dynamic deps
# - disable utmp/wtmp: musl defines bogus paths
# - sandbox=none: avoid seccomp issues in static binaries
RUN ./configure \
    --prefix=/usr \
    --sysconfdir=/etc/ssh \
    --libexecdir=/usr/libexec \
    --with-privsep-path=/var/empty \
    --with-privsep-user=sshd \
    --with-ssl-engine \
    --with-zlib \
    --without-pam \
    --without-selinux \
    --without-kerberos5 \
    --without-libedit \
    --without-ldns \
    --disable-etc-default-login \
    --disable-utmp \
    --disable-wtmp \
    --disable-lastlog \
    --disable-strip \
    --with-sandbox=none \
    --with-ldflags="-static" \
    --with-cflags="-static"

# Build client tools and the server, then strip inside the image.
# sshd-session exists from 9.8; sshd-auth exists from 10.0.
RUN set -eu; \
    targets="ssh scp sftp ssh-keygen ssh-keyscan ssh-add ssh-agent sshd sftp-server"; \
    for extra in sshd-session sshd-auth; do \
        if grep -q "^${extra}"'$(EXEEXT):' Makefile; then \
            targets="$targets $extra"; \
        fi; \
    done; \
    make -j"$(nproc)" $targets; \
    strip $targets
