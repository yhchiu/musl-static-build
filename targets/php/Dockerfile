ARG ALPINE_VERSION=3.20
FROM alpine:${ALPINE_VERSION} AS builder

# Build deps + file(1) for strict static verification
RUN apk update && apk add --no-cache \
    build-base linux-headers autoconf automake libtool bison re2c pkgconf cmake file \
    zlib-dev zlib-static \
    openssl-dev openssl-libs-static \
    oniguruma-dev \
    libxml2-dev libxml2-static \
    sqlite-dev sqlite-static \
    libpng-dev libpng-static \
    libjpeg-turbo-dev libjpeg-turbo-static \
    freetype-dev freetype-static \
    icu-dev icu-static \
    libxslt-dev libxslt-static \
    libsodium-dev libsodium-static \
    bzip2-dev bzip2-static \
    xz-dev xz-static \
    brotli-dev brotli-static \
    libgcrypt-dev libgcrypt-static \
    libgpg-error-dev libgpg-error-static

WORKDIR /usr/src

# Build static libzip
RUN wget https://libzip.org/download/libzip-1.11.2.tar.gz && \
    tar -zxvf libzip-1.11.2.tar.gz && \
    cd libzip-1.11.2 && \
    cmake -DBUILD_SHARED_LIBS=OFF -DCMAKE_INSTALL_PREFIX=/usr \
          -DBUILD_DOC=OFF -DBUILD_EXAMPLES=OFF -DBUILD_REGRESS=OFF -DBUILD_TOOLS=OFF . && \
    make -j$(nproc) && \
    make install

# Build minimal static libcurl
RUN wget https://curl.se/download/curl-8.10.1.tar.gz && \
    tar -zxvf curl-8.10.1.tar.gz && \
    cd curl-8.10.1 && \
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
        --without-nghttp3 && \
    make -j$(nproc) && \
    make install

# Download PHP source
ARG VERSION
RUN wget https://www.php.net/distributions/php-${VERSION}.tar.gz -O php.tar.gz && \
    tar -zxvf php.tar.gz

WORKDIR /usr/src/php-${VERSION}

# Force fully static link (also block C++ runtime dynamic fallback)
ENV PKG_CONFIG="pkgconf --static"
ENV LDFLAGS="-static -static-libgcc -static-libstdc++"
ENV LIBS="-lstdc++"

# Build CLI, CGI, and FPM. phpdbg stays off.
# FPM's systemd, POSIX ACL, and AppArmor hooks stay at their defaults
# (off). The image does not install those libraries.
RUN ./configure \
    --disable-shared \
    --enable-static \
    --enable-cli \
    --enable-cgi \
    --enable-fpm \
    --disable-phpdbg \
    --with-openssl \
    --with-zlib \
    --with-curl \
    --enable-mbstring \
    --enable-xml \
    --enable-bcmath \
    --enable-calendar \
    --enable-exif \
    --enable-ftp \
    --enable-gd \
    --with-freetype \
    --with-jpeg \
    --enable-intl \
    --with-mysqli=mysqlnd \
    --with-pdo-mysql=mysqlnd \
    --with-pdo-sqlite \
    --enable-pcntl \
    --enable-sockets \
    --with-zip \
    --with-xsl \
    --with-sodium \
    --with-bz2

# Build and strip inside the image
RUN make -j$(nproc) LDFLAGS="-all-static -static-libgcc -static-libstdc++" EXTRA_LDFLAGS="-all-static" && \
    strip sapi/cli/php sapi/cgi/php-cgi sapi/fpm/php-fpm
