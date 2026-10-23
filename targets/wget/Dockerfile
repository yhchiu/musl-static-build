ARG ALPINE_VERSION=3.20
FROM alpine:${ALPINE_VERSION} AS builder

RUN apk add --no-cache \
    build-base linux-headers pkgconf file wget ca-certificates \
    openssl-dev openssl-libs-static \
    zlib-dev zlib-static \
    pcre2-dev

WORKDIR /usr/src

ARG VERSION
RUN wget https://ftp.gnu.org/gnu/wget/wget-${VERSION}.tar.gz -O wget.tar.gz && \
    tar -xzf wget.tar.gz

WORKDIR /usr/src/wget-${VERSION}

# Link the executable and all its dependencies statically against musl.
ENV PKG_CONFIG="pkgconf --static"
ENV LDFLAGS="-static"

RUN ./configure \
    --prefix=/usr \
    --disable-nls \
    --disable-iri \
    --disable-rpath \
    --with-ssl=openssl \
    --with-zlib \
    --without-libpsl \
    --without-libuuid \
    --without-metalink

RUN make -j$(nproc) LDFLAGS="-static" && \
    strip src/wget
