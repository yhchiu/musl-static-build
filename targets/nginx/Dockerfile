ARG ALPINE_VERSION=3.20
FROM alpine:${ALPINE_VERSION} AS builder

RUN apk add --no-cache \
    build-base linux-headers pkgconf cmake git file wget ca-certificates \
    openssl-dev openssl-libs-static zlib-dev zlib-static pcre2-dev \
    libxml2-dev libxml2-static libxslt-dev libxslt-static \
    xz-dev xz-static libgcrypt-dev libgcrypt-static libgpg-error-dev libgpg-error-static

# The commit also pins the Brotli submodule. Avoid -march=native so the
# binary does not inherit the build host's optional CPU instructions.
ARG NGX_BROTLI_COMMIT=a71f9312c2deb28875acc7bacfdd5695a111aa53
RUN git clone https://github.com/google/ngx_brotli.git /usr/src/ngx_brotli && \
    git -C /usr/src/ngx_brotli checkout "${NGX_BROTLI_COMMIT}" && \
    git -C /usr/src/ngx_brotli submodule update --init --depth 1 && \
    cmake -S /usr/src/ngx_brotli/deps/brotli -B /usr/src/ngx_brotli/deps/brotli/out \
        -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF \
        -DCMAKE_C_FLAGS="-O2 -fPIC" && \
    cmake --build /usr/src/ngx_brotli/deps/brotli/out --parallel

WORKDIR /usr/src
ARG VERSION
RUN wget https://nginx.org/download/nginx-${VERSION}.tar.gz -O nginx.tar.gz && \
    tar -xzf nginx.tar.gz
WORKDIR /usr/src/nginx-${VERSION}

# Default HTTP modules (proxy/cache, FastCGI, uwsgi, SCGI, rewrite, gzip,
# SSI, access/auth_basic, map, geo, split_clients, limits, upstreams) stay on.
# Every optional module below is built in; no runtime .so loading is used.
RUN ./configure \
        --prefix=/var/lib/nginx \
        --sbin-path=/usr/sbin/nginx \
        --conf-path=/etc/nginx/nginx.conf \
        --pid-path=/var/run/nginx.pid \
        --lock-path=/var/run/nginx.lock \
        --error-log-path=/var/log/nginx/error.log \
        --http-log-path=/var/log/nginx/access.log \
        --http-client-body-temp-path=/var/lib/nginx/client_body \
        --http-proxy-temp-path=/var/lib/nginx/proxy \
        --http-fastcgi-temp-path=/var/lib/nginx/fastcgi \
        --http-uwsgi-temp-path=/var/lib/nginx/uwsgi \
        --http-scgi-temp-path=/var/lib/nginx/scgi \
        --user=nobody --group=nobody \
        --with-cc-opt="-O2 -fno-pie" \
        --with-ld-opt="-static -no-pie $(pkgconf --static --libs libexslt)" \
        --with-threads --with-file-aio --with-pcre-jit \
        --with-http_ssl_module --with-http_v2_module --with-http_v3_module \
        --with-http_realip_module --with-http_addition_module \
        --with-http_xslt_module --with-http_sub_module --with-http_dav_module \
        --with-http_flv_module --with-http_mp4_module \
        --with-http_gunzip_module --with-http_gzip_static_module \
        --with-http_auth_request_module --with-http_random_index_module \
        --with-http_secure_link_module --with-http_slice_module \
        --with-http_stub_status_module \
        --with-stream --with-stream_ssl_module --with-stream_realip_module \
        --with-stream_ssl_preread_module \
        --add-module=/usr/src/ngx_brotli && \
    make -j$(nproc) && strip objs/nginx
