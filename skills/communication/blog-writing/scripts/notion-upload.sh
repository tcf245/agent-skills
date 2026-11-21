#!/usr/bin/env bash
# Send one local file to a Notion MCP file upload.
# Usage: NOTION_UPLOAD_TOKEN=<bearer from create-file-upload> notion-upload.sh <upload_url> <file>
# The bearer is short-lived and single-use; pass it through the environment, not argv.
set -euo pipefail
url="$1"; file="$2"
: "${NOTION_UPLOAD_TOKEN:?set NOTION_UPLOAD_TOKEN to upload_headers.authorization without the Bearer prefix}"
case "$file" in *.png) type=image/png;; *.jpg|*.jpeg) type=image/jpeg;; *.svg) type=image/svg+xml;; *) type=application/octet-stream;; esac
curl -sS --fail-with-body -X POST "$url" -H "authorization: Bearer $NOTION_UPLOAD_TOKEN" -F "file=@$file;type=$type" \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["status"], d["markdown_source"])'
