variable "project_id" {
  description = "Your GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region for deployment"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP Zone (must support T4 GPUs)"
  type        = string
  default     = "us-central1-a"
}

variable "bucket_name" {
  description = "Name of the GCS bucket to store the trained model (must be globally unique)"
  type        = string
}
