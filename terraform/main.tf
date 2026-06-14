terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
  zone    = "${var.gcp_region}-a"
}

resource "google_compute_instance" "thesis_runner" {
  name         = var.runner_name
  machine_type = var.gcp_machine_type

  labels = {
    run_type = var.runner_name
  }

  scheduling {
    provisioning_model  = var.gcp_provisioning_model
    preemptible         = var.gcp_provisioning_model == "SPOT" ? true : false
    automatic_restart   = false
  }

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = 50
      type  = "pd-ssd"
    }
  }

  network_interface {
    network = "default"
    access_config {}
  }

  # 1. Inject the SSH Key into the VM
  metadata = {
    ssh-keys = "${var.ssh_user}:${var.ssh_pub_key}"
  }

  # 2. Pre-install your dependencies (Fixed for Docker Compose v2 & Kernel Builds)
  metadata_startup_script = <<-EOT
    #!/bin/bash
    sudo apt-get update

    sudo apt-get install -y docker.io docker-compose-v2 build-essential libncurses-dev bison flex libssl-dev libelf-dev jq netcat-openbsd

    sudo systemctl enable docker
    sudo systemctl start docker

    sudo usermod -aG docker ${var.ssh_user}

    sudo gpasswd -a ${var.ssh_user} docker
  EOT
}

output "vm_ip" {
  value = google_compute_instance.thesis_runner.network_interface.0.access_config.0.nat_ip
}