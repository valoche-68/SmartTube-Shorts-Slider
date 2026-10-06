#!/bin/sh
# Install missing prerequisites, then run the small configuration assistant.
set -eu

smarttube_find_on_path() {
    smarttube_executable=
    smarttube_probe_name=$1
    shift
    smarttube_search_path=$PATH
    # A broken earlier executable must not hide another working installation.
    # Split on colons without splitting spaces or expanding wildcards in paths.
    while :; do
        smarttube_directory=${smarttube_search_path%%:*}
        if [ -z "$smarttube_directory" ]; then smarttube_directory=.; fi
        if [ -x "$smarttube_directory/$smarttube_probe_name" ] &&
            "$smarttube_directory/$smarttube_probe_name" "$@" >/dev/null 2>&1; then
            smarttube_executable="$smarttube_directory/$smarttube_probe_name"
            return 0
        fi
        case "$smarttube_search_path" in
            *:*) smarttube_search_path=${smarttube_search_path#*:} ;;
            *) return 0 ;;
        esac
    done
}

smarttube_find_python() {
    smarttube_python=
    for smarttube_candidate in python3 python python3.15 python3.14 python3.13 python3.12 python3.11 python3.10; do
        smarttube_find_on_path "$smarttube_candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'
        if [ -n "$smarttube_executable" ]; then
            smarttube_python=$smarttube_executable
            return 0
        fi
    done
}

smarttube_find_adb() {
    smarttube_adb=
    smarttube_find_on_path adb version
    if [ -n "$smarttube_executable" ]; then
        smarttube_adb=$smarttube_executable
        # The Python assistant must resolve this same checked executable.
        PATH="${smarttube_adb%/*}:$PATH"
        export PATH
        return 0
    fi
    # Reuse an explicitly configured Android SDK even if it is not on PATH.
    for smarttube_sdk in "${ANDROID_HOME:-}" "${ANDROID_SDK_ROOT:-}"; do
        if [ -n "$smarttube_sdk" ] && [ -x "$smarttube_sdk/platform-tools/adb" ] &&
            "$smarttube_sdk/platform-tools/adb" version >/dev/null 2>&1; then
            PATH="$smarttube_sdk/platform-tools:$PATH"
            export PATH
            smarttube_adb="$smarttube_sdk/platform-tools/adb"
            return 0
        fi
    done
}

smarttube_admin() {
    if [ "$(id -u)" = 0 ]; then
        "$@"
    elif command -v sudo >/dev/null 2>&1; then
        # Elevate only the package manager, never the assistant.
        sudo "$@"
    else
        printf '%s\n' 'Droits administrateur requis. Installez Python 3.10+ et ADB avec votre gestionnaire de paquets, puis relancez.' >&2
        exit 2
    fi
}

smarttube_install_linux() {
    smarttube_python_package=python3
    smarttube_adb_package=android-tools
    if command -v apt-get >/dev/null 2>&1; then
        smarttube_manager=apt-get
        smarttube_adb_package=adb
    elif command -v dnf >/dev/null 2>&1; then
        smarttube_manager=dnf
    elif command -v pacman >/dev/null 2>&1; then
        smarttube_manager=pacman
        smarttube_python_package=python
    elif command -v zypper >/dev/null 2>&1; then
        smarttube_manager=zypper
    elif command -v apk >/dev/null 2>&1; then
        smarttube_manager=apk
    else
        printf '%s\n' 'Gestionnaire Linux non pris en charge. Installez Python 3.10+ et ADB puis relancez.' >&2
        exit 2
    fi
    set --
    if [ -z "$smarttube_python" ]; then set -- "$@" "$smarttube_python_package"; fi
    if [ "$smarttube_need_adb" = 1 ] && [ -z "$smarttube_adb" ]; then set -- "$@" "$smarttube_adb_package"; fi
    printf '%s\n' "Installation des prerequis manquants avec $smarttube_manager : $*"
    case "$smarttube_manager" in
        apt-get)
            smarttube_admin apt-get update
            smarttube_admin apt-get install -y --no-install-recommends "$@"
            ;;
        dnf) smarttube_admin dnf install -y "$@" ;;
        # Do not refresh just the database (-Sy) or upgrade the whole system (-Syu).
        pacman) smarttube_admin pacman -S --needed --noconfirm "$@" ;;
        zypper) smarttube_admin zypper --non-interactive install "$@" ;;
        apk) smarttube_admin apk add "$@" ;;
    esac
}

smarttube_find_brew() {
    smarttube_brew=
    if command -v brew >/dev/null 2>&1; then
        smarttube_brew=$(command -v brew)
    elif [ -x /opt/homebrew/bin/brew ]; then
        smarttube_brew=/opt/homebrew/bin/brew
    elif [ -x /usr/local/bin/brew ]; then
        smarttube_brew=/usr/local/bin/brew
    fi
}

smarttube_install_macos() {
    smarttube_find_brew
    if [ -z "$smarttube_brew" ]; then
        printf '%s\n' 'Installation de Homebrew depuis sa source officielle. macOS peut demander une validation ou votre mot de passe.'
        curl --fail --silent --show-error --location --proto '=https' --proto-redir '=https' \
            --connect-timeout 15 --max-time 120 --output "$smarttube_tmp/homebrew-install.sh" \
            'https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh'
        /bin/bash "$smarttube_tmp/homebrew-install.sh"
        hash -r
        smarttube_find_brew
    fi
    if [ -z "$smarttube_brew" ]; then
        printf '%s\n' 'Homebrew reste inaccessible. Terminez son installation puis relancez : https://brew.sh/' >&2
        exit 2
    fi
    smarttube_brew_prefix=$("$smarttube_brew" --prefix)
    PATH="$smarttube_brew_prefix/bin:$smarttube_brew_prefix/sbin:$PATH"
    export PATH
    hash -r
    smarttube_find_python
    if [ "$smarttube_need_adb" = 1 ]; then smarttube_find_adb; fi
    if [ -z "$smarttube_python" ]; then
        printf '%s\n' 'Installation de Python avec Homebrew...'
        "$smarttube_brew" install python
    fi
    if [ "$smarttube_need_adb" = 1 ] && [ -z "$smarttube_adb" ]; then
        printf '%s\n' 'Installation de ADB avec Homebrew...'
        "$smarttube_brew" install --cask android-platform-tools
    fi
}

smarttube_need_adb=1
for smarttube_argument do
    case "$smarttube_argument" in -h|--help|--backup|--backup=*) smarttube_need_adb=0 ;; esac
done
smarttube_find_python
smarttube_adb=
if [ "$smarttube_need_adb" = 1 ]; then smarttube_find_adb; fi
if ! command -v curl >/dev/null 2>&1; then
    printf '%s\n' 'curl requis pour le telechargement. Installez curl puis relancez cette commande.' >&2
    exit 2
fi

smarttube_tmp=$(umask 077; mktemp -d "${TMPDIR:-/tmp}/smarttube-assistant.XXXXXXXX")
trap 'rm -rf -- "$smarttube_tmp"' 0
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

if [ -z "$smarttube_python" ] || { [ "$smarttube_need_adb" = 1 ] && [ -z "$smarttube_adb" ]; }; then
    case "$(uname -s)" in
        Linux) smarttube_install_linux ;;
        Darwin) smarttube_install_macos ;;
        *) printf '%s\n' 'Installation automatique non prise en charge sur ce systeme. Installez Python 3.10+ et ADB.' >&2; exit 2 ;;
    esac
    hash -r
    smarttube_find_python
    if [ "$smarttube_need_adb" = 1 ]; then smarttube_find_adb; fi
fi
if [ -z "$smarttube_python" ] || { [ "$smarttube_need_adb" = 1 ] && [ -z "$smarttube_adb" ]; }; then
    printf '%s\n' 'Installation incomplete : Python 3.10+ ou ADB reste inutilisable. Verifiez la version fournie par votre systeme puis relancez.' >&2
    exit 2
fi

curl --fail --silent --show-error --location --proto '=https' --proto-redir '=https' \
    --connect-timeout 15 --max-time 120 \
    --output "$smarttube_tmp/configure_shorts.py" \
    'https://raw.githubusercontent.com/valoche-68/SmartTube-Shorts-Slider/main/tools/configure_shorts.py'

# stdin remains connected to the terminal so input() can read menu answers.
"$smarttube_python" "$smarttube_tmp/configure_shorts.py" "$@"
