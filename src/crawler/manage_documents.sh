#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUCKET="gs://cs288-crawler-html-store"

ALL_DIRS=("crawled_html" "parsed_documents")

usage() {
  echo "Usage: $0 {upload|download} [directory]"
  echo ""
  echo "  upload    Zip and upload directories to GCS (requires gcloud auth)"
  echo "  download  Download zips via public URL (no auth) and unarchive locally"
  echo ""
  echo "  directory  Optional: crawled_html or parsed_documents (default: both)"
  exit 1
}

resolve_dirs() {
  if [ -z "${1:-}" ]; then
    DIRS=("${ALL_DIRS[@]}")
  else
    local found=false
    for d in "${ALL_DIRS[@]}"; do
      if [ "$1" = "$d" ]; then found=true; break; fi
    done
    if ! $found; then
      echo "Error: unknown directory '$1'. Must be one of: ${ALL_DIRS[*]}"
      exit 1
    fi
    DIRS=("$1")
  fi
}

upload() {
  echo "=== Uploading to $BUCKET ==="
  for dir in "${DIRS[@]}"; do
    src="$SCRIPT_DIR/$dir"
    zip_file="$SCRIPT_DIR/${dir}.zip"

    if [ ! -d "$src" ]; then
      echo "Warning: $src does not exist, skipping."
      continue
    fi

    echo "Zipping $dir ..."
    (cd "$SCRIPT_DIR" && zip -r -q "$zip_file" "$dir")

    echo "Uploading ${dir}.zip to $BUCKET ..."
    gsutil cp "$zip_file" "$BUCKET/${dir}.zip"

    echo "Making ${dir}.zip publicly readable ..."
    gsutil acl ch -u AllUsers:R "$BUCKET/${dir}.zip"

    rm -f "$zip_file"
    echo "Done: $dir"
  done
  echo ""
  echo "=== Public download URLs ==="
  for dir in "${DIRS[@]}"; do
    echo "  https://storage.googleapis.com/${BUCKET#gs://}/${dir}.zip"
  done
}

download() {
  echo "=== Downloading from public URLs ==="
  for dir in "${DIRS[@]}"; do
    url="https://storage.googleapis.com/${BUCKET#gs://}/${dir}.zip"
    zip_file="$SCRIPT_DIR/${dir}.zip"

    echo "Downloading ${dir}.zip ..."
    curl -fSL -o "$zip_file" "$url"

    echo "Unzipping ${dir}.zip ..."
    unzip -o -q "$zip_file" -d "$SCRIPT_DIR"

    # rm -f "$zip_file"
    echo "Done: $dir"
  done
}

if [ $# -lt 1 ] || [ $# -gt 2 ]; then
  usage
fi

resolve_dirs "${2:-}"

case "$1" in
  upload)   upload ;;
  download) download ;;
  *)        usage ;;
esac
