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
}

data "google_compute_zones" "available" {
  region = var.gcp_region
  status = "UP"
}

resource "google_compute_instance" "thesis_runner" {
  name         = var.runner_name
  machine_type = var.gcp_machine_type

  zone         = data.google_compute_zones.available.names[0]

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

  metadata = {
    ssh-keys = "${var.ssh_user}:${var.ssh_pub_key}"
  }

  metadata_startup_script = <<-EOT
    #!/bin/bash
    export DEBIAN_FRONTEND=noninteractive
    sudo apt-get update

    # Basis-Abhängigkeiten installieren
    sudo apt-get install -y build-essential libncurses-dev bison flex libssl-dev libelf-dev jq netcat-openbsd

    # 1. Versuch: Aus den GCP-Instanzmetadaten lesen
    WORKLOAD=$(curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/attributes/workload | tr '[:upper:]' '[:lower:]')

    # 2. Versuch: Falls API leer ist, nimm die direkte Terraform-Variable als Fallback
    if [ -z "$WORKLOAD" ]; then
        WORKLOAD="${lower(var.workload)}"
    fi

    echo "Detected Workload for Docker check: $WORKLOAD"

    if [ "$WORKLOAD" = "mid" ]; then
        echo "Installing Docker for MID workload..."
        sudo apt-get install -y docker.io docker-compose-v2
        sudo systemctl enable docker
        sudo systemctl start docker
        sudo usermod -aG docker ${var.ssh_user}
        sudo gpasswd -a ${var.ssh_user} docker

        sudo chmod 666 /var/run/docker.sock
    else
        echo "Skipping Docker installation. Workload is: $WORKLOAD"
    fi

    # Signalisiere der Pipeline, dass ALLES fertig ist
    touch /tmp/startup_finished
  EOT
}

output "vm_ip" {
  value = google_compute_instance.thesis_runner.network_interface.0.access_config.0.nat_ip
}