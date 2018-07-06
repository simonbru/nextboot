#!/bin/bash

cd "$(dirname "$0")"
OUTPUT=${1:-uefi_nextboot_linux.pyz}

tmpfolder="$(mktemp -d)"
cleanup() {
    rm -r "$tmpfolder"
}
trap cleanup EXIT

pip install -r <(pipenv lock -r) --target "$tmpfolder"
cp uefi_nextboot.py "$tmpfolder"/
python -m zipapp "$tmpfolder" \
    --output "$OUTPUT" \
    --main 'uefi_nextboot:main' \
    -p '/usr/bin/env python3'
chmod +x "$OUTPUT"

echo "Successfully built ${OUTPUT}"
