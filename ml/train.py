import os
import sys
import json
import random
import numpy as np
import pandas as pd
from PIL import Image
from typing import Dict, Any

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import torchvision.models as models
from torchvision.models import EfficientNet_B0_Weights, ResNet50_Weights
from sklearn.metrics import f1_score, accuracy_score

from ml.preprocessing.pipeline import get_transforms

def set_seed(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

class MessidorDataset(Dataset):
    def __init__(self, csv_path: str, transform=None):
        self.df = pd.read_csv(csv_path)
        self.transform = transform

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img_path = row["full_image_path"]
        label = int(row["diagnosis"])
        
        try:
            image = Image.open(img_path).convert("RGB")
        except Exception as e:
            # Fallback black image if file read error occurs
            image = Image.new("RGB", (224, 224), color=0)
            
        if self.transform:
            image = self.transform(image)
            
        return image, label

def get_device():
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    elif torch.cuda.is_available():
        return torch.device("cuda")
    else:
        return torch.device("cpu")

def build_model(num_classes: int = 5, architecture: str = "EfficientNet-B0"):
    if architecture == "ResNet50":
        model = models.resnet50(weights=ResNet50_Weights.DEFAULT)
        in_features = model.fc.in_features
        model.fc = nn.Linear(in_features, num_classes)
    else:
        model = models.efficientnet_b0(weights=EfficientNet_B0_Weights.DEFAULT)
        in_features = model.classifier[1].in_features
        model.classifier[1] = nn.Linear(in_features, num_classes)
    return model

def compute_class_weights(df: pd.DataFrame, num_classes: int = 5) -> torch.Tensor:
    counts = df["diagnosis"].value_counts().to_dict()
    total_samples = len(df)
    weights = []
    for c in range(num_classes):
        count = counts.get(c, 1)
        # Smooth inverse class weighting
        w = total_samples / (num_classes * count)
        weights.append(w)
    weights = torch.tensor(weights, dtype=torch.float32)
    return weights / weights.sum() * num_classes

def train_model(
    output_dir: str = "ml",
    epochs: int = 12,
    batch_size: int = 32,
    learning_rate: float = 3e-4,
    architecture: str = "EfficientNet-B0"
) -> Dict[str, Any]:
    set_seed(42)
    device = get_device()
    print(f"Training on compute device: {device}")

    splits_dir = os.path.join(output_dir, "data_splits")
    train_csv = os.path.join(splits_dir, "train.csv")
    val_csv = os.path.join(splits_dir, "validation.csv")

    if not os.path.exists(train_csv) or not os.path.exists(val_csv):
        from ml.dataset import inspect_and_prepare_dataset
        inspect_and_prepare_dataset(output_dir)

    train_df = pd.read_csv(train_csv)

    train_dataset = MessidorDataset(train_csv, transform=get_transforms(is_training=True))
    val_dataset = MessidorDataset(val_csv, transform=get_transforms(is_training=False))

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)

    model = build_model(num_classes=5, architecture=architecture).to(device)
    
    class_weights = compute_class_weights(train_df, num_classes=5).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_val_f1 = -1.0
    best_model_state = None
    best_epoch = -1

    history = {
        "epoch": [],
        "train_loss": [],
        "train_acc": [],
        "val_loss": [],
        "val_acc": [],
        "val_macro_f1": []
    }

    models_dir = os.path.join(output_dir, "models")
    os.makedirs(models_dir, exist_ok=True)

    print(f"Starting training ({epochs} epochs, batch_size={batch_size})...")

    for epoch in range(1, epochs + 1):
        # --- Training Loop ---
        model.train()
        running_loss = 0.0
        correct_train = 0
        total_train = 0

        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            preds = outputs.argmax(dim=1)
            correct_train += (preds == labels).sum().item()
            total_train += images.size(0)

        scheduler.step()

        train_loss = running_loss / total_train
        train_acc = correct_train / total_train

        # --- Validation Loop ---
        model.eval()
        val_loss = 0.0
        val_preds_all = []
        val_labels_all = []

        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)
                val_loss += loss.item() * images.size(0)

                preds = outputs.argmax(dim=1)
                val_preds_all.extend(preds.cpu().numpy())
                val_labels_all.extend(labels.cpu().numpy())

        val_loss = val_loss / len(val_dataset)
        val_acc = accuracy_score(val_labels_all, val_preds_all)
        val_macro_f1 = f1_score(val_labels_all, val_preds_all, average="macro", zero_division=0)

        history["epoch"].append(epoch)
        history["train_loss"].append(round(train_loss, 4))
        history["train_acc"].append(round(train_acc, 4))
        history["val_loss"].append(round(val_loss, 4))
        history["val_acc"].append(round(val_acc, 4))
        history["val_macro_f1"].append(round(val_macro_f1, 4))

        print(f"Epoch {epoch}/{epochs} - Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f} | Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}, Val Macro F1: {val_macro_f1:.4f}")

        if val_macro_f1 > best_val_f1:
            best_val_f1 = val_macro_f1
            best_epoch = epoch
            best_model_state = model.state_dict().copy()

    # Save Best Model Checkpoint
    best_model_path = os.path.join(models_dir, "dr_model_best.pth")
    torch.save(best_model_state, best_model_path)

    # Save Training History and Metadata
    with open(os.path.join(models_dir, "training_history.json"), "w") as f:
        json.dump(history, f, indent=2)

    config = {
        "architecture": architecture,
        "epochs": epochs,
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "best_epoch": best_epoch,
        "best_val_macro_f1": round(best_val_f1, 4),
        "device": str(device)
    }
    with open(os.path.join(models_dir, "training_config.json"), "w") as f:
        json.dump(config, f, indent=2)

    label_map = {
        "0": "No DR",
        "1": "Mild NPDR",
        "2": "Moderate NPDR",
        "3": "Severe NPDR",
        "4": "Proliferative DR"
    }
    with open(os.path.join(models_dir, "label_mapping.json"), "w") as f:
        json.dump(label_map, f, indent=2)

    metadata = {
        "model_version": "netradrishti-dr-v1",
        "dataset": "MESSIDOR-2",
        "architecture": architecture,
        "classes": 5,
        "training_samples": len(train_df),
        "best_epoch": best_epoch,
        "best_val_macro_f1": round(best_val_f1, 4),
        "torch_version": torch.__version__
    }
    with open(os.path.join(models_dir, "model_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Training completed! Best model saved to {best_model_path} (Best Val Macro F1: {best_val_f1:.4f} at epoch {best_epoch})")
    return metadata

if __name__ == "__main__":
    train_model()
