"""RE-THREAD: Reusable ResNet-18 Classifier Training Script.

Trains ImageNet-pretrained ResNet-18 for:
- Task A: Condition (new, gently_used, worn, heavily_worn)
- Task B: Material (natural, synthetic, blend)

Usage:
    python ml/train_resnet18_classifier.py --task condition --data-dir /path/to/dataset --epochs 25
    python ml/train_resnet18_classifier.py --task material --data-dir /path/to/dataset --epochs 25
"""

import argparse
import os
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.transforms as transforms
from torchvision.datasets import ImageFolder
from torchvision.models import resnet18, ResNet18_Weights
from torch.utils.data import DataLoader
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix

TASK_CONFIGS = {
    "condition": {
        "classes": ["new", "gently_used", "worn", "heavily_worn"],
        "save_name": "condition.pt",
    },
    "material": {
        "classes": ["natural", "synthetic", "blend"],
        "save_name": "material.pt",
    },
}


def train_resnet18(
    task: str,
    data_dir: str,
    epochs: int = 25,
    batch_size: int = 32,
    lr: float = 1e-4,
    output_dir: str = "weights",
):
    if task not in TASK_CONFIGS:
        raise ValueError(f"Task '{task}' must be 'condition' or 'material'.")

    cfg = TASK_CONFIGS[task]
    class_names = cfg["classes"]
    save_filename = cfg["save_name"]

    print("=" * 60)
    print(f"Training ResNet-18 for Task: {task.upper()}")
    print(f"Target classes ({len(class_names)}): {class_names}")
    print(f"Data directory: {data_dir}")
    print("=" * 60)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Standard ImageNet transforms
    train_transform = transforms.Compose([
        transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.15),
        transforms.RandomRotation(degrees=15),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

    val_transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

    train_path = os.path.join(data_dir, "train")
    val_path = os.path.join(data_dir, "val")

    if not os.path.exists(train_path):
        print(f"Warning: train directory not found at {train_path}.")
        return

    train_dataset = ImageFolder(train_path, transform=train_transform)
    val_dataset = ImageFolder(val_path, transform=val_transform)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=2)

    # 1. Load Pretrained ResNet-18
    model = resnet18(weights=ResNet18_Weights.DEFAULT)
    num_features = model.fc.in_features
    model.fc = nn.Linear(num_features, len(class_names))
    model = model.to(device)

    # 2. Balanced class weights
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-2)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_macro_f1 = 0.0
    best_weights = None

    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * images.size(0)

        scheduler.step()
        train_loss = running_loss / len(train_dataset)

        # Validation
        model.eval()
        all_preds, all_labels = [], []
        with torch.no_grad():
            for images, labels in val_loader:
                images = images.to(device)
                outputs = model(images)
                preds = torch.argmax(outputs, dim=1).cpu().numpy()
                all_preds.extend(preds)
                all_labels.extend(labels.numpy())

        acc = accuracy_score(all_labels, all_preds)
        macro_f1 = f1_score(all_labels, all_preds, average="macro", zero_division=0)
        print(f"Epoch [{epoch}/{epochs}] - Loss: {train_loss:.4f} | Val Acc: {acc:.4f} | Macro-F1: {macro_f1:.4f}")

        if macro_f1 > best_macro_f1:
            best_macro_f1 = macro_f1
            best_weights = model.state_dict().copy()

    # Save to weights directory
    os.makedirs(output_dir, exist_ok=True)
    target_file = os.path.join(output_dir, save_filename)
    payload = {
        "model_state_dict": best_weights if best_weights else model.state_dict(),
        "class_names": class_names,
        "num_classes": len(class_names),
        "task": task,
    }
    torch.save(payload, target_file)
    print("=" * 60)
    print(f"Successfully saved {task} model to: {target_file}")
    print(f"Best Macro-F1: {best_macro_f1:.4f}")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train ResNet-18 vision classifier")
    parser.add_argument("--task", type=str, required=True, choices=["condition", "material"])
    parser.add_argument("--data-dir", type=str, required=True, help="Path containing train/ and val/ folders")
    parser.add_argument("--epochs", type=int, default=25)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--output-dir", type=str, default="weights")
    args = parser.parse_args()

    train_resnet18(
        task=args.task,
        data_dir=args.data_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        output_dir=args.output_dir,
    )
