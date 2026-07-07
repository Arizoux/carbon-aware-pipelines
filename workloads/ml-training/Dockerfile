FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y wget tar && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

ENV PYTHONUNBUFFERED=1

RUN mkdir -p ./data && \
    wget -qO ./data/cifar-10-python.tar.gz https://huggingface.co/datasets/cifar10/resolve/main/cifar-10-python.tar.gz && \
    tar -xzf ./data/cifar-10-python.tar.gz -C ./data/ && \
    rm ./data/cifar-10-python.tar.gz

COPY train.py .

CMD ["python", "train.py"]