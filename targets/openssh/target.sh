#!/bin/bash

TARGET_DESCRIPTION="OpenSSH"
DEFAULT_VERSION="9.9p2"
VERSION_PATTERN='^([89]|10)\.[0-9]+p[0-9]+$'
VERSION_HELP="8.xpN, 9.xpN, or 10.xpN (e.g. 8.9p1, 9.9p2, 10.6p1)"
ALPINE_VERSION="3.20"
ARTIFACTS=(
    "ssh:ssh" "scp:scp" "sftp:sftp" "ssh-keygen:ssh-keygen"
    "ssh-keyscan:ssh-keyscan" "ssh-add:ssh-add" "ssh-agent:ssh-agent"
    "sshd:sshd" "sftp-server:sftp-server"
    "sshd-session:sshd-session" "sshd-auth:sshd-auth"
)

target_prepare() {
    local major minor selected=() artifact name
    major="${VERSION%%.*}"
    minor="${VERSION#*.}"
    minor="${minor%%p*}"

    # OpenSSH 8.x needs OpenSSL 1.1; 9.x and 10.x can use OpenSSL 3.
    if [[ "$VERSION" =~ ^8\. ]]; then
        ALPINE_VERSION="3.16"
    fi

    # 9.8 split the listener from sshd-session. 10.0 split authentication
    # into sshd-auth. Earlier releases keep that work inside sshd.
    for artifact in "${ARTIFACTS[@]}"; do
        name="${artifact#*:}"
        case "$name" in
            sshd-session)
                if (( major > 9 || (major == 9 && minor >= 8) )); then
                    selected+=("$artifact")
                fi
                ;;
            sshd-auth)
                if (( major >= 10 )); then
                    selected+=("$artifact")
                fi
                ;;
            *)
                selected+=("$artifact")
                ;;
        esac
    done
    ARTIFACTS=("${selected[@]}")
}
