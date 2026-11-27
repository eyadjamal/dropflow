#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
if [ -x "$HERE/DropFlow" ]; then
    exec "$HERE/DropFlow" "$@"
fi
exec python3 "$HERE/DropFlow.pyw" "$@"
