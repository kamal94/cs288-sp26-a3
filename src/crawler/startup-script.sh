#!/bin/bash
set -e

# Read DB credentials from instance metadata
METADATA="http://metadata.google.internal/computeMetadata/v1/instance/attributes"
H="Metadata-Flavor: Google"
export DATABASE_HOST=$(curl -sf -H "$H" $METADATA/db-host)
export DATABASE_PORT=$(curl -sf -H "$H" $METADATA/db-port)
export DATABASE_NAME=$(curl -sf -H "$H" $METADATA/db-name)
export DATABASE_USER=$(curl -sf -H "$H" $METADATA/db-user)
export DATABASE_PASSWORD=$(curl -sf -H "$H" $METADATA/db-password)
export BUCKET_NAME=$(curl -sf -H "$H" $METADATA/bucket-name)

# Pull latest code (repo and venv are pre-installed in the image)
sudo git config --system --add safe.directory /app
sudo git -C /app pull

# Run crawler
/app/venv/bin/python /app/src/crawler/crawl.py
