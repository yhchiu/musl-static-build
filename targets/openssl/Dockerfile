ARG ALPINE_VERSION=3.20
FROM alpine:${ALPINE_VERSION} AS builder

RUN apk add --no-cache \
    build-base linux-headers perl file wget ca-certificates

WORKDIR /usr/src

ARG VERSION
RUN wget https://github.com/openssl/openssl/releases/download/openssl-${VERSION}/openssl-${VERSION}.tar.gz -O openssl.tar.gz && \
    tar -xzf openssl.tar.gz

WORKDIR /usr/src/openssl-${VERSION}

# Providers are linked into libcrypto. -static makes apps/openssl a static file.
# The default certificate store is /etc/ssl (cert.pem and certs/).
RUN ./Configure linux-x86_64 no-shared no-module no-tests \
        --prefix=/usr --openssldir=/etc/ssl \
        -static && \
    make -j$(nproc) && \
    strip apps/openssl
