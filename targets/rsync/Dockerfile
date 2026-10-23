ARG ALPINE_VERSION=3.20
FROM alpine:${ALPINE_VERSION} AS builder

RUN apk add --no-cache \
    build-base linux-headers pkgconf file wget ca-certificates \
    openssl-dev openssl-libs-static \
    zlib-dev zlib-static \
    zstd-dev zstd-static \
    lz4-dev lz4-static

WORKDIR /usr/src

# Alpine 3.20 has no xxhash-static package. Build the static library here.
ARG XXHASH_VERSION=0.8.3
RUN wget https://github.com/Cyan4973/xxHash/archive/refs/tags/v${XXHASH_VERSION}.tar.gz -O xxhash.tar.gz && \
    tar -xzf xxhash.tar.gz && \
    make -C xxHash-${XXHASH_VERSION} libxxhash.a && \
    install -D xxHash-${XXHASH_VERSION}/libxxhash.a /usr/local/lib/libxxhash.a && \
    install -D xxHash-${XXHASH_VERSION}/xxhash.h /usr/local/include/xxhash.h

ARG VERSION
RUN wget https://download.samba.org/pub/rsync/rsync-${VERSION}.tar.gz -O rsync.tar.gz && \
    tar -xzf rsync.tar.gz

WORKDIR /usr/src/rsync-${VERSION}

# Included popt. System static zlib, OpenSSL, zstd, and lz4.
# Leave ACL, xattrs, and iconv off.
ENV LDFLAGS="-static"
RUN ./configure \
    --prefix=/usr \
    --disable-md2man \
    --disable-locale \
    --disable-iconv \
    --disable-idn \
    --disable-acl-support \
    --disable-xattr-support \
    --with-included-popt \
    --with-included-zlib=no \
    LIBS="-pthread" \
    --enable-openssl \
    --enable-xxhash \
    --enable-zstd \
    --enable-lz4

RUN make -j$(nproc) LDFLAGS="-static" && \
    strip rsync
