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
    workload = var.workload
  }

  metadata_startup_script = <<-EOT
    #!/bin/bash
    export DEBIAN_FRONTEND=noninteractive

    # Warte auf Standard-Ubuntu Cloud-Init Locks
    while sudo fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do
      echo "Waiting for background apt updates to finish..."
      sleep 5
    done

    # Metadaten sicher abrufen und in Kleinbuchstaben konvertieren
    WORKLOAD=$(curl -sf -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/attributes/workload | tr '[:upper:]' '[:lower:]')

    if [ -z "$WORKLOAD" ]; then
        WORKLOAD="${lower(var.workload)}"
    fi

    echo "Detected Workload in Startup Script: $WORKLOAD"

    # Überprüfen, ob es sich um den minimalen Check handelt
    if [ "$WORKLOAD" = "short" ] || [ "$WORKLOAD" = "hello-world" ]; then
        echo "Minimaler Workload erkannt. Installiere nur Netcat fürs Pipeline-Polling."
        sudo apt-get update && sudo apt-get install -y netcat-openbsd

        # Sofort beenden und Signal-File schreiben
        touch /tmp/startup_finished
        exit 0
    fi

    # =========================================================================
    # AB HIER: Höhere Workloads (MID / LONG) bekommen schwerere Abhängigkeiten
    # =========================================================================

    sudo apt-get update

    # 1. Compiler-Werkzeuge für Kernel-Build (MID oder LONG, je nachdem wie du es planst)
    # Falls du Docker für das CNN nutzt, braucht das CNN diese Pakete lokal evtl. gar nicht.
    sudo apt-get install -y build-essential libncurses-dev bison flex libssl-dev libelf-dev jq netcat-openbsd

    # 2. Docker Installation nur für Container-Workloads
    if [ "$WORKLOAD" = "mid" ] || [ "$WORKLOAD" = "long" ]; then
        echo "Installing Docker for Container Workload..."
        while sudo fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do sleep 3; done

        sudo apt-get install -y docker.io docker-compose-v2
        sudo systemctl enable docker
        sudo systemctl start docker
        sudo usermod -aG docker ${var.ssh_user}
        sudo chmod 666 /var/run/docker.sock
    fi

    # Signalisiere der Pipeline das erfolgreiche Ende der Provisionierung
    touch /tmp/startup_finished
  EOT
}

output "vm_ip" {
  value = google_compute_instance.thesis_runner.network_interface.0.access_config.0.nat_ip
}