#!/bin/sh
# Build event and prefork in separate trees. A static httpd holds one MPM.
# "most" selects mod_cgid for event and mod_cgi for prefork.
set -eu

out="/usr/src/httpd-${VERSION}/static-bin"
mkdir -p "$out"

build_mpm() {
    mpm="$1"
    httpd_name="$2"
    tree="$3"
    cd "$tree"
    LDFLAGS="-static -no-pie" CFLAGS="-O2 -fno-pie" ./configure \
        --prefix=/usr \
        --sysconfdir=/etc/httpd \
        --with-apr=/usr/local/apr \
        --with-apr-util=/usr/local/apr \
        --with-pcre=/usr \
        --with-ssl=/usr \
        --with-nghttp2=/usr \
        --with-brotli=/usr \
        --with-mpm="$mpm" \
        --enable-mods-static=most \
        --enable-ssl \
        --enable-ssl-staticlib-deps \
        --enable-http2 \
        --enable-nghttp2-staticlib-deps \
        --enable-proxy-http2 \
        --enable-brotli \
        --enable-dav-lock \
        --enable-heartbeat \
        --enable-heartmonitor \
        --disable-so \
        --disable-md \
        --disable-lua \
        --enable-static-htpasswd
    make -j"$(nproc)" LDFLAGS="-all-static -no-pie"
    if [ -f .libs/httpd ]; then
        cp -a .libs/httpd "$out/$httpd_name"
    else
        cp -a httpd "$out/$httpd_name"
    fi
}

build_mpm event httpd "/usr/src/httpd-${VERSION}"
if [ -f support/.libs/htpasswd ]; then
    cp -a support/.libs/htpasswd "$out/htpasswd"
else
    cp -a support/htpasswd "$out/htpasswd"
fi
build_mpm prefork httpd-prefork "/usr/src/httpd-${VERSION}-prefork"
strip "$out/httpd" "$out/httpd-prefork" "$out/htpasswd"
