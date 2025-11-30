#!/bin/bash
set -euo pipefail

mkdir -p .local
LOCKFILE=.local/download.lock

if [[ -f "${LOCKFILE}" ]] && kill -0 "$(cat "${LOCKFILE}" || true)" 2>/dev/null; then
	echo Still running
	exit 1
fi

echo $$ > "${LOCKFILE}"

DISTRIB_FILE=distrib.json
DISTRIB=$(cat ${DISTRIB_FILE})
CDN_URL="https://cdn-11.eft-store.com"
UNPACKED_URI=$(echo ${DISTRIB} | jq -r '.unpackedUri')
BASE_URL=${CDN_URL}${UNPACKED_URI}

mkdir -p .cache
wget ${BASE_URL}GameAssembly.dll -O .cache/GameAssembly.dll
wget ${BASE_URL}EscapeFromTarkov.exe -O .cache/EscapeFromTarkov.exe