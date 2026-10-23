ARG ALPINE_VERSION=3.20
FROM alpine:${ALPINE_VERSION} AS builder

RUN apk add --no-cache \
    build-base linux-headers pkgconf file wget ca-certificates \
    openssl-dev openssl-libs-static \
    zlib-dev zlib-static \
    pcre2-dev

WORKDIR /usr/src

# Small static libcurl for git-remote-https. No HTTP/2, Brotli, or IDN.
# This is not the curl target, and it does not use the openssl target.
ARG CURL_VERSION=8.10.1
RUN wget https://curl.se/download/curl-${CURL_VERSION}.tar.gz && \
    tar -xzf curl-${CURL_VERSION}.tar.gz && \
    cd curl-${CURL_VERSION} && \
    ./configure --prefix=/usr \
        --disable-shared \
        --enable-static \
        --with-openssl \
        --with-zlib \
        --without-brotli \
        --without-zstd \
        --without-libpsl \
        --without-libidn2 \
        --without-libssh2 \
        --without-nghttp2 \
        --without-ngtcp2 \
        --without-nghttp3 \
        --disable-docs \
        --disable-manual \
        --without-ca-embed && \
    make -j$(nproc) && \
    make install

ARG VERSION
RUN wget https://www.kernel.org/pub/software/scm/git/git-${VERSION}.tar.gz -O git.tar.gz && \
    tar -xzf git.tar.gz

WORKDIR /usr/src/git-${VERSION}

COPY build.sh /tmp/build-git.sh
RUN VERSION="${VERSION}" sh /tmp/build-git.sh
