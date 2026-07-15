#!/bin/bash
set -e

WORKLOAD=${1:-short}

echo "===================================================="
echo "🌍 CARBON-AWARE PIPELINE: STARTING WORKLOAD"
echo "===================================================="
echo "📍 GCP Zone: $(curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/zone | awk -F/ '{print $NF}')"
echo "🖥️ Machine: $(curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/machine-type | awk -F/ '{print $NF}')"
echo "📦 Selected Workload: ${WORKLOAD^^}"
echo "===================================================="

START_TIME=$(date +%s)

if [ "$WORKLOAD" = "short" ]; then
    echo "⚡ Running Short Workload (Hello World)..."
    sleep 5
    echo "✅ Hello World Check passed."

elif [ "$WORKLOAD" = "mid" ]; then
    echo "🐳 Running Mid Workload (Machine Learning Model Training)..."
    cd workloads/ml-training

    echo "⚙️ Configuring Docker Buildx environment..."
    sudo docker buildx create --name thesis-builder --use --driver docker-container 2>/dev/null || sudo docker buildx use thesis-builder
    sudo docker buildx inspect --bootstrap

    echo "🔨 Building Docker Image with Buildx via Compose..."
    DOCKER_BUILDKIT=1 sudo docker compose build --no-cache

    echo "🧠 Running Neural Network Training Loop..."
    sudo docker compose up --abort-on-container-exit

    echo "🛑 Cleaning up..."
    sudo docker compose down

elif [ "$WORKLOAD" = "long" ]; then
    echo "🐧 Running Long Workload (Linux Kernel Compilation)..."
    KERNEL_VERSION="6.8.4"

    echo "⬇️ Downloading Linux Kernel v${KERNEL_VERSION}..."
    wget -q https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-${KERNEL_VERSION}.tar.xz

    echo "📦 Extracting Archive..."
    tar -xf linux-${KERNEL_VERSION}.tar.xz
    cd linux-${KERNEL_VERSION}

    echo "⚙️ Configuring Build (defconfig)..."
    make defconfig

    echo "🔨 Compiling Kernel with $(nproc) cores..."
    make -j$(nproc)

    echo "✅ Kernel compiled successfully."

else
    echo "Unknown Workload: $WORKLOAD"
    exit 1
fi

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo "===================================================="
echo "🚀 Pipeline Finished Successfully!"
echo "⏱️ Total Run Time (E_run phase): ${DURATION} seconds"
echo "===================================================="