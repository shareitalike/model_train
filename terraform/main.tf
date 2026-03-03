terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# 1. Bucket to store the final model weights
resource "google_storage_bucket" "model_bucket" {
  name          = var.bucket_name
  location      = "US"
  force_destroy = true # Allows deleting the bucket even if it has contents
}

# 2. Service Account for the VM so it can upload files and delete itself
resource "google_service_account" "kaithi_sa" {
  account_id   = "kaithi-trainer-sa"
  display_name = "Kaithi OCR Auto-Trainer SA"
}

# Grant the SA access to upload to the Storage Bucket
resource "google_project_iam_member" "sa_storage_admin" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.kaithi_sa.email}"
}

# Grant the SA access to delete itself (compute instance admin)
resource "google_project_iam_member" "sa_compute_admin" {
  project = var.project_id
  role    = "roles/compute.instanceAdmin.v1"
  member  = "serviceAccount:${google_service_account.kaithi_sa.email}"
}

# Grant the SA the Service Account User role, necessary for instances running as an SA to delete themselves
resource "google_project_iam_member" "sa_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${google_service_account.kaithi_sa.email}"
}

# 3. The Trainer VM (Preemptible + High RAM CPU)
resource "google_compute_instance" "kaithi_trainer" {
  name         = "kaithi-ocr-trainer"
  machine_type = "e2-standard-8" # 8 vCPUs, 32GB RAM
  zone         = var.zone

  # Cost Protection: Preemptible instances are ~70% cheaper
  scheduling {
    preemptible       = true
    automatic_restart = false
  }

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = 100 # 100GB matches runbook requirement
      type  = "pd-ssd"
    }
    # Cost Protection: Delete disk when VM is destroyed
    auto_delete = true
  }

  network_interface {
    network = "default"
    access_config {
      # Ephemeral IP
    }
  }

  service_account {
    email  = google_service_account.kaithi_sa.email
    scopes = ["cloud-platform"]
  }

  # 4. Fully Automated Startup Script
  metadata_startup_script = <<-EOF
#!/bin/bash
# Redirect all output to a log file for monitoring
exec > >(tee -a /var/log/startup-script.log) 2>&1

echo "========================================="
echo "Starting Automated CPU Kaithi OCR Training..."
echo "========================================="

# 1. Update and install dependencies
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y docker.io docker-compose git zip make linux-headers-$(uname -r)

# 2. Skip GPU installation for Free Tier CPU machine
echo "Configuring for CPU-only Training..."
systemctl stop docker
systemctl start docker

# 3. Clone the repo and setup
echo "Cloning Repository..."
cd /opt
git clone https://github.com/your-org/kaithi-ocr.git
cd kaithi-ocr
cp backend/.env.example backend/.env

# Add docker permission
usermod -aG docker root

# 4. Run the Training Pipeline Unattended
echo "Starting Training Pipeline (CPU Mode)..."
make up

echo "Generating Synthetic Data..."
make synth-data

echo "Training the Model (This will take a long time on CPU...)"
make train
# The above commands are synchronous, the script will wait here until training finishes.

# 5. Package the Results
echo "Packaging Model..."
zip -r my_trained_model.zip ./models/kaithi-trocr-v1/

# 6. Upload to GCS Bucket
echo "Uploading to GCS..."
HOME=/root
gsutil cp my_trained_model.zip "gs://${var.bucket_name}/"

# 7. Self-Destruction
echo "========================================="
echo "Training Complete. Initiating Self-Destruction in 60 seconds..."
echo "========================================="
sleep 60
gcloud compute instances delete kaithi-ocr-trainer --zone="${var.zone}" --quiet
  EOF

  tags = ["allow-ssh"]
}

# Firewall rule to allow SSH access for monitoring logs if needed
resource "google_compute_firewall" "allow_ssh" {
  name    = "allow-ssh-kaithi-auto"
  network = "default"
  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["allow-ssh"]
}
