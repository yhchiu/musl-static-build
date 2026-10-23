ARG ALPINE_VERSION=3.20
FROM alpine:${ALPINE_VERSION} AS builder

RUN apk add --no-cache \
    build-base linux-headers pkgconf file wget ca-certificates \
    openssl-dev openssl-libs-static \
    zlib-dev zlib-static \
    expat-dev expat-static \
    pcre2-dev \
    nghttp2-dev nghttp2-static \
    brotli-dev brotli-static

# APR releases are pinned for every httpd 2.4.x build.
ENV APR_VERSION=1.7.6 \
    APU_VERSION=1.6.5

WORKDIR /usr/src

RUN wget https://archive.apache.org/dist/apr/apr-${APR_VERSION}.tar.gz -O apr.tar.gz && \
    wget https://archive.apache.org/dist/apr/apr-util-${APU_VERSION}.tar.gz -O apr-util.tar.gz && \
    tar -xzf apr.tar.gz && \
    tar -xzf apr-util.tar.gz

# Build static APR without DSO support. A fully static httpd cannot dlopen.
WORKDIR /usr/src/apr-${APR_VERSION}
RUN CFLAGS="-O2 -fno-pie" LDFLAGS="-no-pie" ./configure \
        --prefix=/usr/local/apr \
        --disable-shared \
        --enable-static \
        --disable-dso && \
    make -j$(nproc) && \
    make install

# Bundle sdbm and Expat. Leave LDAP, SQL drivers, and APR crypto out so
# those modules are not linked against extra libraries.
WORKDIR /usr/src/apr-util-${APU_VERSION}
RUN CFLAGS="-O2 -fno-pie" LDFLAGS="-no-pie" ./configure \
        --prefix=/usr/local/apr \
        --with-apr=/usr/local/apr \
        --with-expat=/usr \
        --disable-shared \
        --enable-static \
        --disable-util-dso \
        --with-dbm=sdbm && \
    make -j$(nproc) && \
    make install

ARG VERSION
WORKDIR /usr/src
RUN wget https://archive.apache.org/dist/httpd/httpd-${VERSION}.tar.gz -O httpd.tar.gz && \
    tar -xzf httpd.tar.gz && \
    cp -a httpd-${VERSION} httpd-${VERSION}-prefork

WORKDIR /usr/src/httpd-${VERSION}

# Compile common modules into each httpd. mod_so stays off: musl static
# binaries cannot load modules at runtime.
# ssl, deflate, brotli, and http2 come from the installed static libraries.
# dav_lock, heartbeat, and heartmonitor are enabled with the DAV and
# proxy modules from "most".
# mod_md, Lua, and LDAP stay off (they need curl/jansson, Lua, or OpenLDAP).
# build-mpms.sh configures event and prefork in separate source trees.
ENV PKG_CONFIG="pkgconf --static"
COPY build-mpms.sh /tmp/build-mpms.sh
RUN VERSION="${VERSION}" sh /tmp/build-mpms.sh
