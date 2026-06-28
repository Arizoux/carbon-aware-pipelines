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

    while sudo fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do
      echo "Waiting for background apt updates to finish..."
      sleep 5
    done

    sudo apt-get update
    sudo apt-get install -y build-essential libncurses-dev bison flex libssl-dev libelf-dev jq netcat-openbsd

    # 2. Metadaten sicher abrufen (das -f sorgt dafür, dass Fehler wirklich leer zurückkommen, statt "Not Found")
    WORKLOAD=$(curl -sf -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/attributes/workload | tr '[:upper:]' '[:lower:]')

    # Falls leer, greife sicher auf die Terraform-Variable zurück
    if [ -z "$WORKLOAD" ]; then
        WORKLOAD="${lower(var.workload)}"
    fi

    echo "Detected Workload for Docker check: $WORKLOAD"

    if [ "$WORKLOAD" = "mid" ]; then
        echo "Installing Docker for MID workload..."

        # Erneuter Check, falls das apt-Lock wieder zugeschlagen hat
        while sudo fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do sleep 3; done

        sudo apt-get install -y docker.io docker-compose-v2
        sudo systemctl enable docker
        sudo systemctl start docker
        sudo usermod -aG docker ${var.ssh_user}
        sudo chmod 666 /var/run/docker.sock
    else
        echo "Skipping Docker installation. Workload is: $WORKLOAD"
    fi

    # Signalisiere der Pipeline, dass ALLES erfolgreich installiert wurde
    touch /tmp/startup_finished
  EOT
}

output "vm_ip" {
  value = google_compute_instance.thesis_runner.network_interface.0.access_config.0.nat_ip
}