FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

ENV PYTHONUNBUFFERED=1

RUN python -c "import torchvision; torchvision.datasets.CIFAR10(root='./data', train=True, download=True)"

COPY train.py .

CMD ["python", "train.py"]