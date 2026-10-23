ARG ALPINE_VERSION=3.20
FROM alpine:${ALPINE_VERSION} AS builder

RUN apk add --no-cache \
    build-base linux-headers pkgconf file wget ca-certificates \
    openssl-dev openssl-libs-static \
    zlib-dev zlib-static \
    nghttp2-dev nghttp2-static

WORKDIR /usr/src

ARG VERSION
RUN wget https://curl.se/download/curl-${VERSION}.tar.gz -O curl.tar.gz && \
    tar -xzf curl.tar.gz

WORKDIR /usr/src/curl-${VERSION}

# Link the executable and all its dependencies statically against musl.
ENV PKG_CONFIG="pkgconf --static"
ENV LDFLAGS="-static"

RUN ./configure \
    --prefix=/usr \
    --disable-shared \
    --enable-static \
    --with-openssl \
    --with-zlib \
    --with-nghttp2 \
    --with-ca-bundle=/etc/ssl/certs/ca-certificates.crt \
    --with-ca-path=/etc/ssl/certs \
    --without-brotli \
    --without-zstd \
    --without-libpsl \
    --without-libidn2 \
    --without-libssh2 \
    --without-libssh \
    --without-gssapi \
    --without-ngtcp2 \
    --without-nghttp3 \
    --disable-ldap \
    --disable-ldaps

RUN make -j$(nproc) LDFLAGS="-all-static" && \
    strip src/curl
