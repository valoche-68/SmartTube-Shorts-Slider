#!/bin/sh
# Download the small configuration assistant without cloning the Android project.
set -eu

smarttube_python=
for smarttube_candidate in python3 python; do
    if command -v "$smarttube_candidate" >/dev/null 2>&1 &&
        "$smarttube_candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
        smarttube_python=$smarttube_candidate
        break
    fi
done
if [ -z "$smarttube_python" ]; then
    printf '%s\n' 'Python 3.10+ requis / required: https://www.python.org/downloads/' \
        'Installez Python, puis recopiez la commande de lancement.' >&2
    exit 2
fi
if ! command -v curl >/dev/null 2>&1; then
    printf '%s\n' 'curl requis / required. Installez curl puis relancez cette commande.' >&2
    exit 2
fi

umask 077
smarttube_tmp=$(mktemp -d "${TMPDIR:-/tmp}/smarttube-assistant.XXXXXXXX")
trap 'rm -rf -- "$smarttube_tmp"' 0
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

curl --fail --silent --show-error --location --proto '=https' --proto-redir '=https' \
    --connect-timeout 15 --max-time 120 \
    --output "$smarttube_tmp/configure_shorts.py" \
    'https://raw.githubusercontent.com/valoche-68/SmartTube-Shorts-Slider/main/tools/configure_shorts.py'

# stdin remains connected to the terminal so input() can read menu answers.
"$smarttube_python" "$smarttube_tmp/configure_shorts.py" "$@"
