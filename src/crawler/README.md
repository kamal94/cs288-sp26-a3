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
export REPO_URL="https://github.com/kamal94/cs288-sp26-a3.git"
export DB_HOST="35.238.181.136"
export DB_PORT="5432"
export DB_NAME="crawler"
export DB_USER="postgres"
export DB_PASSWORD="3mt-cR|~E]u_Gr61"
export BUCKET_NAME="cs288-a3-crawled-html"

gcloud compute instances create crawler-vm \
  --provisioning-model=SPOT \
  --instance-termination-action=STOP \
  --machine-type=e2-micro \
  --zone=us-central1-a \
  --image=crawler-base-image \
  --scopes=cloud-platform \
  --metadata=db-host=$DB_HOST,db-port=$DB_PORT,db-name=$DB_NAME,db-user=$DB_USER,db-password=$DB_PASSWORD,bucket-name=$BUCKET_NAME \
  --metadata-from-file=startup-script=startup-script.sh
```

> - `--scopes=cloud-platform` gives the VM access to GCS via its service account (no key file needed)
> - `--instance-termination-action=STOP` keeps the disk on preemption so you can restart cheaply
> - To launch multiple crawlers, change `crawler-vm` to `crawler-vm-1`, `crawler-vm-2`, etc.
