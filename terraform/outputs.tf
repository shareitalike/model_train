output "model_bucket_name" {
  description = "The GCS bucket where the trained model will be uploaded."
  value       = google_storage_bucket.model_bucket.name
}

output "trainer_ip" {
  description = "The ephemeral public IP of the trainer VM (for SSH access if needed to view logs)."
  value       = google_compute_instance.kaithi_trainer.network_interface.0.access_config.0.nat_ip
}
