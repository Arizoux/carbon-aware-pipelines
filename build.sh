#!/bin/bash
# Exit on error
set -e

echo "===================================================="
echo "🌍 CARBON-AWARE PIPELINE: HELLO WORLD CHECK"
echo "===================================================="
echo "✅ VM Successfully Provisioned"
echo "✅ SSH Connection Established"
echo "📍 GCP Region: $(curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/zone | awk -F/ '{print $NF}')"
echo "🖥️ Machine Type: $(curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/machine-type | awk -F/ '{print $NF}')"
echo "🕒 Time on VM: $(date)"
echo "===================================================="


# Microservices
if [ -f "docker-compose.yml" ]; then
    echo "📦 Docker Compose found. Starting build..."
    sudo docker compose build
    sudo docker compose up -d
    sudo docker compose run tests
fi

# Kernel/C Project
if [ -f "Makefile" ]; then
    echo "🛠️ Makefile found. Starting compilation..."
    make -j$(nproc)
fi

echo "🚀 Test Sequence Finished Successfully!"