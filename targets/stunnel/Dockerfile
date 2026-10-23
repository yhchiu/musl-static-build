ARG ALPINE_VERSION=3.20
FROM alpine:${ALPINE_VERSION} AS builder

RUN apk add --no-cache \
    build-base linux-headers pkgconf file wget ca-certificates \
    openssl-dev openssl-libs-static zlib-dev zlib-static

WORKDIR /usr/src
ARG VERSION
RUN (wget https://www.stunnel.org/downloads/stunnel-${VERSION}.tar.gz -O stunnel.tar.gz || \
     wget https://www.stunnel.org/downloads/archive/5.x/stunnel-${VERSION}.tar.gz -O stunnel.tar.gz) && \
    tar -xzf stunnel.tar.gz
WORKDIR /usr/src/stunnel-${VERSION}

# libwrap, systemd and dynamically loaded engines are not needed for the
# standalone TLS proxy. Configuration and CA certificates stay external.
ENV PKG_CONFIG="pkgconf --static"
RUN LDFLAGS="-static" ./configure \
        --prefix=/usr --sysconfdir=/etc --localstatedir=/var \
        --with-ssl=/usr --disable-shared --enable-static \
        --disable-libwrap --disable-systemd --disable-fips && \
    make -j$(nproc) LDFLAGS="-all-static" && \
    mkdir -p static-bin && \
    if [ -f src/.libs/stunnel ]; then cp src/.libs/stunnel static-bin/stunnel; \
    else cp src/stunnel static-bin/stunnel; fi && \
    strip static-bin/stunnel
