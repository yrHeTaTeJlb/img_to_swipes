#! /bin/bash
#
# shellcheck disable=SC2086

set -u

ORIGINAL_PKG='com.dtmilano.android.culebratester2'
PKG=${CULEBRATESTER2_PKG:-$ORIGINAL_PKG}
PKGRE=${PKG//\./\\.}

usage() {
    printf '%s' "$usage"
    exit 1
}

fatal() {
    args="$*"
    printf '⛔️ %sERROR: %s%s\n' "$red" "$args" "$sgr0" >&2
    exit 1
}

_help() {
    printf '%s' "$usage"
    printf '\n'
    printf 'positional arguments:\n'
    printf ' forward-port                 uses adb to forward port %d\n' "$port"
    printf '     [--local-port PORT] [--remote-port PORT]\n'
    printf ' run-instrumentation          runs the instrumentation and starts the server\n'
    printf ' start-server                 starts the server on the device\n'
    printf ' install                      installs on device\n'
    printf ' uninstall                    uninstalls pkgs on device\n'
    printf '\n'
    printf 'optional arguments:\n'
    printf ' -h, --help                   show this help message and exit\n'
    printf ' -n, --dryrun                 does not execute the commands\n'
    printf ' -v, --verbose                prints verbose output\n'
    printf ' -s, --serialno SERIALNO      use the specific device\n'
    exit 0
}

check_device() {
    if ! adb $D get-state &> /dev/null; then
        fatal "Cannot connect to device: $D"
    fi
}

check_installed() {
    pkgs=$(adb $D shell pm list packages --user 0)
    # shellcheck disable=SC2181
    if [[ $? -ne 0 ]]; then
        fatal 'Cannot get the installed packages.'
    fi
    n=$(grep -c "$PKGRE" <<<"$pkgs")
    case "$n" in
        0)
            fatal 'app and instrumentation apks should be installed. None found.'
            ;;

        1)
            # we are missing one
            if ! grep "$PKGRE\.test\$" <<<"$pkgs"; then
                fatal 'app found but instrumentation apk has not been installed.'
            fi

            if ! grep "$PKGRE\$" <<<"$pkgs"; then
                fatal 'instrumentation found but app apk has not been installed.'
            fi
            ;;

        2)
            :
            ;;

        *)
            fatal "unexpected number of matching apks installed: $n"
            ;;
    esac
}

forward_port() {
    local local_port=$port
    local remote_port=$port

    while [[ $# -ge 1 ]]; do
        case "$1" in
            '--local-port')
                shift
                if [[ $# -lt 1 ]]; then
                    fatal 'Missing PORT in forward-port'
                fi
                local_port=$1
                ;;

            '--remote-port')
                shift
                if [[ $# -lt 1 ]]; then
                    fatal 'Missing PORT in forward-port'
                fi
                remote_port=$1
                ;;

            *)
                fatal "Invalid option to forward-port: $1"
                ;;
        esac
        shift
    done

    [[ "$verbose" == true ]] && printf 'Forwarding port local:%d => remote:%d\n' "$local_port" "$remote_port"
    # adb forward [--no-rebind] LOCAL REMOTE
    if ! $dryrun adb $D forward tcp:"$local_port" tcp:"$remote_port"; then
        fatal "Could not forward port local:$local_port remote:$remote_port"
    fi
}

run_instrumentation() {
    printf '%s🐍 Starting CulebraTester2-public service...%s\n' "$green" "$sgr0"
    # grant [--user USER_ID] [--all-permissions] PACKAGE PERMISSION
    $dryrun adb $D shell pm grant --user 0 "$PKG" 'android.permission.DUMP' && \
    $dryrun adb $D shell pm grant --user 0 "$PKG" 'android.permission.PACKAGE_USAGE_STATS' && \
    $dryrun adb $D shell pm grant --user 0 "$PKG" 'android.permission.CHANGE_CONFIGURATION' && \
    $dryrun adb $D shell am instrument -w -r -e debug false -e class "$ORIGINAL_PKG.UiAutomatorHelper" \
                "$PKG.test/androidx.test.runner.AndroidJUnitRunner"
}

uninstall_pkgs() {
    $dryrun adb $D uninstall "$PKG.test" && adb $D uninstall "$PKG"
}

get_adb_devices() {
    command adb devices 2>&1 | tail -n +2 | sed '/^$/d'
}

android_select_device() {
    DEV=$(get_adb_devices)
    if [ -z "$DEV" ]
    then
        printf '⛔️ %sERROR: There is no locally connected devices%s\n' "$red" "$sgr0" >&2
        exit 1
    fi

    if grep -q 'daemon started successfully' <<<"$DEV"
    then
        # try again
        DEV=$(get_adb_devices)
    fi

    N=$(wc -l <<<"$DEV" | sed 's/ //g')
    case "$N" in
    1)
        # only one device detected
        D=$DEV
        ;;

    *)
        # more than one device detected
        OLDIFS=$IFS
        IFS="
    "
        PS3="Select the device to use, <Q> to quit: "
        select D in $DEV
        do
            [ "$REPLY" = 'q' -o "$REPLY" = 'Q' ] && exit 2
            [ -n "$D" ] && break
        done < /dev/tty

        IFS=$OLDIFS
        ;;
    esac

    if [ -z "$D" ]
    then
        printf '⛔️ %sERROR: Target device could not be determined%s\n' "$red" "$sgr0" >&2
        exit 1
    fi

    # this didn't work on Darwin
    # echo "-s ${D%% *}"
    printf -- '-s %s\n' "$(echo ${D} | sed 's/ .*$//')"
}


if [[ "$0" =~ ^/dev/fd ]]; then
    progname='culebratester2'
else
    progname="$(basename "$0")"
fi
port=9987
if [[ -n "$TERM" ]] && type tput &>/dev/null; then
    smul=$(tput smul)
    rmul=$(tput rmul)
    red=$(tput setaf 1)
    green=$(tput setaf 2)
    sgr0=$(tput sgr0)
else
    smul=
    rmul=
    red=
    green=
    sgr0=
fi
printf -v usage 'usage: %s [-h|--help] [-v|--verbose] [-x|--debig] [-n|-dryrun] [-s|--serialno SERIALNO] {%sf%sorward-port | %sr%sun-instrumentation | %ss%start-server | %si%snstall | %su%sninstall }\n' "$progname" \
        "$smul" "$rmul" "$smul" "$rmul" "$smul" "$rmul" "$smul" "$rmul" "$smul" "$rmul"

for arg in "$@"; do
  shift
  case "$arg" in
    '--help')
        set -- "$@" '-h'
        ;;
    '--verbose')
        set -- "$@" '-v'
        ;;
    '--debug')
        set -- "$@" '-x'
        ;;
    '--dryrun')
        set -- "$@" '-n'
        ;;
    '--serialno')
        set -- "$@" '-s'
        ;;
    *)
        set -- "$@" "$arg"
        ;;
  esac
done

# Default behavior
verbose=false
debug=false
dryrun=
serialno=

OPTIND=1
while getopts ":hvxns:" opt
do
  case "$opt" in
    'h')
        _help
        ;;

    'v')
        verbose=true
        ;;

    'x')
        debug=true
        ;;

	'n')
		dryrun='echo'
		;;

    's')
        serialno="$OPTARG"
        ;;
    '?')
        usage
        ;;
  esac
done
shift $(( OPTIND - 1 ))

[[ "$debug" == true ]] && set -x

if [[ -n "${serialno}" ]]; then
    D="-s ${serialno}"
else
    D=$(android_select_device)
fi

check_device
check_installed
forward_port "$@" && run_instrumentation