FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

COPY train.py .

# Starte das Skript
CMD ["python", "train.py"]