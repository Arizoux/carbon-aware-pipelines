import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
import time
import os


def main():
    print("🧠 Starting ML Workload: Training CNN on CIFAR-10")

    num_cores = os.cpu_count()
    torch.set_num_threads(num_cores)
    print(f"🖥️ PyTorch is utilizing {num_cores} CPU cores for training.")

    transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.5,), (0.5,))])
    trainset = torchvision.datasets.CIFAR10(root='./data', train=True, download=False, transform=transform)
    trainloader = torch.utils.data.DataLoader(trainset, batch_size=64, shuffle=True, num_workers=2)

    model = nn.Sequential(
        nn.Conv2d(3, 32, 3, padding=1), nn.ReLU(),
        nn.MaxPool2d(2, 2),
        nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(),
        nn.MaxPool2d(2, 2),
        nn.Flatten(),
        nn.Linear(64 * 8 * 8, 512), nn.ReLU(),
        nn.Linear(512, 10)
    )

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    EPOCHS = 40
    start_time = time.time()

    for epoch in range(EPOCHS):
        running_loss = 0.0
        for i, data in enumerate(trainloader, 0):
            inputs, labels = data
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()

        print(f"🔄 Epoch {epoch + 1}/{EPOCHS} complete. Loss: {running_loss / len(trainloader):.3f}")

    print(f"✅ Training finished in {time.time() - start_time:.2f} seconds.")


if __name__ == "__main__":
    main()