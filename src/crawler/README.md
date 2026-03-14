# Crawler Setup

## Google Cloud Storage Bucket

HTML content from crawled pages is stored in a GCS bucket. Run the following to create and configure it:

```bash
export BUCKET_NAME="your-bucket-name"

# Create the bucket
gcloud storage buckets create gs://$BUCKET_NAME \
  --location=us-central1 \
  --uniform-bucket-level-access

# Allow public GET access
gcloud storage buckets add-iam-policy-binding gs://$BUCKET_NAME \
  --member=allUsers \
  --role=roles/storage.objectViewer

# Grant write access to the VM service account
gcloud storage buckets add-iam-policy-binding gs://$BUCKET_NAME \
  --member=serviceAccount:$(gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)")-compute@developer.gserviceaccount.com \
  --role=roles/storage.objectCreator
```

> Replace `your-bucket-name` with your desired bucket name. The last command uses the default Compute Engine service account, which covers all VMs in the project.

## Spot VM (Crawler Instance)

DB credentials are passed as instance metadata and read by the startup script at boot.

```bash
export REPO_URL="https://github.com/YOUR_ORG/cs288-sp26-a3.git"
export DB_HOST="YOUR_DB_HOST"
export DB_PORT="5432"
export DB_NAME="YOUR_DB_NAME"
export DB_USER="YOUR_DB_USER"
export DB_PASSWORD="YOUR_DB_PASSWORD"
export BUCKET_NAME="your-bucket-name"

gcloud compute instances create crawler-vm \
  --provisioning-model=SPOT \
  --instance-termination-action=STOP \
  --machine-type=e2-micro \
  --zone=us-central1-a \
  --scopes=cloud-platform \
  --metadata=\
db-host=$DB_HOST,\
db-port=$DB_PORT,\
db-name=$DB_NAME,\
db-user=$DB_USER,\
db-password=$DB_PASSWORD,\
repo-url=$REPO_URL,\
startup-script='#!/bin/bash
set -e

# Read DB credentials from instance metadata
METADATA="http://metadata.google.internal/computeMetadata/v1/instance/attributes"
H="Metadata-Flavor: Google"
export DATABASE_HOST=$(curl -sf -H "$H" $METADATA/db-host)
export DATABASE_PORT=$(curl -sf -H "$H" $METADATA/db-port)
export DATABASE_NAME=$(curl -sf -H "$H" $METADATA/db-name)
export DATABASE_USER=$(curl -sf -H "$H" $METADATA/db-user)
export DATABASE_PASSWORD=$(curl -sf -H "$H" $METADATA/db-password)
export REPO_URL=$(curl -sf -H "$H" $METADATA/repo-url)
export BUCKET_NAME=$(curl -sf -H "$H" $METADATA/bucket-name)

# Install dependencies
apt-get update -q && apt-get install -y -q python3-pip git

# Clone repo and install Python packages
git clone "$REPO_URL" /app
pip3 install -r /app/src/crawler/requirements.txt

# Run crawler
python3 /app/src/crawler/crawl.py'
```

> - `--scopes=cloud-platform` gives the VM access to GCS via its service account (no key file needed)
> - `--instance-termination-action=STOP` keeps the disk on preemption so you can restart cheaply
> - To launch multiple crawlers, change `crawler-vm` to `crawler-vm-1`, `crawler-vm-2`, etc.
