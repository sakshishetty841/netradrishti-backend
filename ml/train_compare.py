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
from torch.utils.data import DataLoader
from sklearn.metrics import f1_score, accuracy_score, recall_score, precision_recall_fscore_support

from ml.preprocessing.pipeline import get_transforms
from ml.train import MessidorDataset, build_model, get_device, set_seed, compute_class_weights
from ml.losses import FocalLoss, WeightedFocalLoss

def train_and_eval_loss_variant(
    variant_name: str,
    loss_fn_builder,
    train_loader: DataLoader,
    val_loader: DataLoader,
    train_df: pd.DataFrame,
    device: torch.device,
    epochs: int = 20,
    learning_rate: float = 3e-4
) -> Dict[str, Any]:
    set_seed(42)
    model = build_model(num_classes=5, architecture="EfficientNet-B0").to(device)
    
    loss_fn = loss_fn_builder(device)
    optimizer = optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_val_macro_f1 = -1.0
    best_model_state = None
    best_epoch = -1
    best_val_per_class = {}

    history = []

    print(f"\n==========================================")
    print(f"  Training Strategy: {variant_name}")
    print(f"==========================================")

    for epoch in range(1, epochs + 1):
        # --- Train Loop ---
        model.train()
        running_loss = 0.0
        correct_train = 0
        total_train = 0

        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = loss_fn(outputs, labels)
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
                loss = loss_fn(outputs, labels)
                val_loss += loss.item() * images.size(0)

                preds = outputs.argmax(dim=1)
                val_preds_all.extend(preds.cpu().numpy())
                val_labels_all.extend(labels.cpu().numpy())

        val_loss = val_loss / len(val_loader.dataset)
        val_acc = accuracy_score(val_labels_all, val_preds_all)
        val_macro_f1 = f1_score(val_labels_all, val_preds_all, average="macro", zero_division=0)
        
        prec, rec, f1s, _ = precision_recall_fscore_support(
            val_labels_all, val_preds_all, average=None, labels=[0, 1, 2, 3, 4], zero_division=0
        )

        epoch_metrics = {
            "epoch": epoch,
            "train_loss": round(train_loss, 4),
            "train_acc": round(train_acc, 4),
            "val_loss": round(val_loss, 4),
            "val_acc": round(val_acc, 4),
            "val_macro_f1": round(val_macro_f1, 4),
            "g3_recall": round(float(rec[3]), 4),
            "g4_recall": round(float(rec[4]), 4)
        }
        history.append(epoch_metrics)

        print(f"Epoch {epoch:02d}/{epochs:02d} | Train Loss: {train_loss:.4f}, Acc: {train_acc:.4f} | Val Loss: {val_loss:.4f}, Acc: {val_acc:.4f}, Macro F1: {val_macro_f1:.4f} (G3 Rec: {rec[3]:.2f}, G4 Rec: {rec[4]:.2f})")

        if val_macro_f1 > best_val_macro_f1:
            best_val_macro_f1 = val_macro_f1
            best_epoch = epoch
            best_model_state = model.state_dict().copy()
            best_val_per_class = {
                "precision": [round(float(p), 4) for p in prec],
                "recall": [round(float(r), 4) for r in rec],
                "f1": [round(float(f), 4) for f in f1s]
            }

    return {
        "variant_name": variant_name,
        "best_epoch": best_epoch,
        "best_val_macro_f1": round(best_val_macro_f1, 4),
        "best_val_per_class": best_val_per_class,
        "best_model_state": best_model_state,
        "history": history
    }

def run_model_comparison(output_dir: str = "ml", epochs: int = 20, batch_size: int = 32) -> Dict[str, Any]:
    set_seed(42)
    device = get_device()
    print(f"Running Round 2 Model Comparison on compute device: {device}")

    splits_dir = os.path.join(output_dir, "data_splits")
    train_csv = os.path.join(splits_dir, "train.csv")
    val_csv = os.path.join(splits_dir, "validation.csv")

    train_df = pd.read_csv(train_csv)

    train_dataset = MessidorDataset(train_csv, transform=get_transforms(is_training=True))
    val_dataset = MessidorDataset(val_csv, transform=get_transforms(is_training=False))

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)

    class_weights = compute_class_weights(train_df, num_classes=5).to(device)

    # 1. Model A: Weighted Cross Entropy
    def builder_a(dev):
        return nn.CrossEntropyLoss(weight=class_weights)

    # 2. Model B: Focal Loss (gamma=2.0)
    def builder_b(dev):
        return FocalLoss(gamma=2.0)

    # 3. Model C: Weighted Focal Loss (gamma=2.0, inverse weights)
    def builder_c(dev):
        return WeightedFocalLoss(alpha=class_weights, gamma=2.0)

    res_a = train_and_eval_loss_variant("Model A (Weighted Cross Entropy)", builder_a, train_loader, val_loader, train_df, device, epochs=epochs)
    res_b = train_and_eval_loss_variant("Model B (Focal Loss gamma=2.0)", builder_b, train_loader, val_loader, train_df, device, epochs=epochs)
    res_c = train_and_eval_loss_variant("Model C (Weighted Focal Loss)", builder_c, train_loader, val_loader, train_df, device, epochs=epochs)

    results = [res_a, res_b, res_c]

    # Select winning model strictly based on Validation Macro F1 score
    winning = max(results, key=lambda x: x["best_val_macro_f1"])
    print(f"\n=======================================================")
    print(f" WINNING STRATEGY (VALIDATION F1): {winning['variant_name']}")
    print(f" Best Validation Macro F1: {winning['best_val_macro_f1']} at epoch {winning['best_epoch']}")
    print(f"=======================================================")

    models_dir = os.path.join(output_dir, "models")
    os.makedirs(models_dir, exist_ok=True)

    # Save winning model weights to dr_model_best.pth
    best_model_path = os.path.join(models_dir, "dr_model_best.pth")
    torch.save(winning["best_model_state"], best_model_path)

    # Save comparison summary
    comparison_summary = {
        "selected_strategy": winning["variant_name"],
        "strategy_comparison": [
            {
                "strategy": r["variant_name"],
                "best_epoch": r["best_epoch"],
                "val_macro_f1": r["best_val_macro_f1"],
                "val_g3_recall": r["best_val_per_class"]["recall"][3],
                "val_g4_recall": r["best_val_per_class"]["recall"][4]
            }
            for r in results
        ]
    }
    with open(os.path.join(models_dir, "model_comparison_results.json"), "w") as f:
        json.dump(comparison_summary, f, indent=2)

    with open(os.path.join(models_dir, "training_history.json"), "w") as f:
        json.dump(winning["history"], f, indent=2)

    config = {
        "architecture": "EfficientNet-B0",
        "selected_strategy": winning["variant_name"],
        "epochs": epochs,
        "batch_size": batch_size,
        "best_epoch": winning["best_epoch"],
        "best_val_macro_f1": winning["best_val_macro_f1"],
        "device": str(device)
    }
    with open(os.path.join(models_dir, "training_config.json"), "w") as f:
        json.dump(config, f, indent=2)

    metadata = {
        "model_version": "netradrishti-dr-v2",
        "dataset": "MESSIDOR-2",
        "architecture": "EfficientNet-B0",
        "selected_loss_strategy": winning["variant_name"],
        "classes": 5,
        "training_samples": len(train_df),
        "best_epoch": winning["best_epoch"],
        "best_val_macro_f1": winning["best_val_macro_f1"],
        "torch_version": torch.__version__
    }
    with open(os.path.join(models_dir, "model_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    return comparison_summary

if __name__ == "__main__":
    run_model_comparison()
