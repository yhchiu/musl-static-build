#!/bin/sh
# Build the git binaries that this target exports.
# gitexecdir and bindir are both the relative path "git", so a directory
# named git that holds these files is the runtime exec-path.
set -eu

make -j"$(nproc)" \
    prefix=/usr \
    bindir=/usr/git \
    gitexecdir=git \
    RUNTIME_PREFIX=YesPlease \
    NO_GETTEXT=YesPlease \
    NO_PERL=YesPlease \
    NO_TCLTK=YesPlease \
    NO_PYTHON=YesPlease \
    NO_RUST=YesPlease \
    NO_EXPAT=YesPlease \
    NO_REGEX=NeedsStartEnd \
    USE_LIBPCRE2=YesPlease \
    LDFLAGS="-static" \
    CURL_LDFLAGS="$(pkgconf --static --libs libcurl)" \
    git \
    git-shell \
    git-http-backend \
    git-remote-http \
    git-remote-https \
    git-receive-pack \
    git-upload-pack \
    git-upload-archive

strip \
    git \
    git-shell \
    git-http-backend \
    git-remote-http \
    git-remote-https \
    git-receive-pack \
    git-upload-pack \
    git-upload-archive
