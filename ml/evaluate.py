import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

import torch
from torch.utils.data import DataLoader
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support, confusion_matrix, classification_report
)

from ml.preprocessing.pipeline import get_transforms
from ml.train import MessidorDataset, build_model, get_device

LABEL_NAMES = ["No DR", "Mild NPDR", "Moderate NPDR", "Severe NPDR", "Proliferative DR"]

ROUND1_TEST_METRICS = {
    "accuracy": 0.6336,
    "macro_precision": 0.6632,
    "macro_recall": 0.5872,
    "macro_f1": 0.5936,
    "weighted_f1": 0.6505,
    "per_class_recall": {
        "No DR": 0.6928,
        "Mild NPDR": 0.3902,
        "Moderate NPDR": 0.6346,
        "Severe NPDR": 0.8182,
        "Proliferative DR": 0.4000
    }
}

def evaluate_model(output_dir: str = "ml") -> dict:
    device = get_device()
    print(f"Evaluating Round 2 model on device: {device}")

    models_dir = os.path.join(output_dir, "models")
    reports_dir = os.path.join(output_dir, "reports")
    splits_dir = os.path.join(output_dir, "data_splits")

    model_path = os.path.join(models_dir, "dr_model_best.pth")
    test_csv = os.path.join(splits_dir, "test.csv")

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Trained model checkpoint not found at {model_path}")
    if not os.path.exists(test_csv):
        raise FileNotFoundError(f"Test split CSV not found at {test_csv}")

    config_path = os.path.join(models_dir, "training_config.json")
    arch = "EfficientNet-B0"
    strategy = "Unknown Strategy"
    if os.path.exists(config_path):
        with open(config_path) as f:
            cfg = json.load(f)
            arch = cfg.get("architecture", "EfficientNet-B0")
            strategy = cfg.get("selected_strategy", "Unknown Strategy")

    model = build_model(num_classes=5, architecture=arch).to(device)
    state_dict = torch.load(model_path, map_location=device)
    model.load_state_dict(state_dict)
    model.eval()

    test_dataset = MessidorDataset(test_csv, transform=get_transforms(is_training=False))
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False, num_workers=0)

    test_preds_all = []
    test_probs_all = []
    test_labels_all = []

    softmax = torch.nn.Softmax(dim=1)

    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(device)
            outputs = model(images)
            probs = softmax(outputs)
            preds = outputs.argmax(dim=1)

            test_probs_all.extend(probs.cpu().numpy().tolist())
            test_preds_all.extend(preds.cpu().numpy().tolist())
            test_labels_all.extend(labels.numpy().tolist())

    accuracy = accuracy_score(test_labels_all, test_preds_all)
    precision, recall, f1, support = precision_recall_fscore_support(
        test_labels_all, test_preds_all, average=None, labels=[0, 1, 2, 3, 4], zero_division=0
    )
    
    macro_prec = float(np.mean(precision))
    macro_rec = float(np.mean(recall))
    macro_f1 = float(np.mean(f1))
    weighted_f1 = float(np.average(f1, weights=support))

    cm = confusion_matrix(test_labels_all, test_preds_all, labels=[0, 1, 2, 3, 4])

    specificity_per_class = []
    for i in range(5):
        tp = cm[i, i]
        fn = np.sum(cm[i, :]) - tp
        fp = np.sum(cm[:, i]) - tp
        tn = np.sum(cm) - (tp + fn + fp)
        spec = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
        specificity_per_class.append(round(spec, 4))

    per_class_metrics = {}
    for idx, name in enumerate(LABEL_NAMES):
        per_class_metrics[name] = {
            "grade": idx,
            "support": int(support[idx]),
            "precision": round(float(precision[idx]), 4),
            "recall_sensitivity": round(float(recall[idx]), 4),
            "specificity": specificity_per_class[idx],
            "f1_score": round(float(f1[idx]), 4)
        }

    test_metrics = {
        "model_architecture": arch,
        "selected_loss_strategy": strategy,
        "eval_dataset": "MESSIDOR-2 Held-Out Test Set",
        "total_test_samples": len(test_labels_all),
        "accuracy": round(float(accuracy), 4),
        "macro_precision": round(macro_prec, 4),
        "macro_recall": round(macro_rec, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "per_class_metrics": per_class_metrics,
        "confusion_matrix": cm.tolist()
    }

    # Save Test Metrics JSON
    with open(os.path.join(reports_dir, "test_metrics.json"), "w") as f:
        json.dump(test_metrics, f, indent=2)

    # Save Classification Report Text / Dict
    clf_report = classification_report(
        test_labels_all, test_preds_all, target_names=LABEL_NAMES, output_dict=True, zero_division=0
    )
    with open(os.path.join(reports_dir, "classification_report.json"), "w") as f:
        json.dump(clf_report, f, indent=2)

    # Save Round 1 vs Round 2 Comparison JSON
    comparison_metrics = {
        "summary": {
            "accuracy": {"round1": ROUND1_TEST_METRICS["accuracy"], "round2": round(float(accuracy), 4)},
            "macro_precision": {"round1": ROUND1_TEST_METRICS["macro_precision"], "round2": round(macro_prec, 4)},
            "macro_recall": {"round1": ROUND1_TEST_METRICS["macro_recall"], "round2": round(macro_rec, 4)},
            "macro_f1": {"round1": ROUND1_TEST_METRICS["macro_f1"], "round2": round(macro_f1, 4)},
            "weighted_f1": {"round1": ROUND1_TEST_METRICS["weighted_f1"], "round2": round(weighted_f1, 4)}
        },
        "per_class_recall": {
            name: {
                "round1": ROUND1_TEST_METRICS["per_class_recall"][name],
                "round2": round(float(recall[idx]), 4)
            }
            for idx, name in enumerate(LABEL_NAMES)
        }
    }
    with open(os.path.join(reports_dir, "round1_vs_round2_comparison.json"), "w") as f:
        json.dump(comparison_metrics, f, indent=2)

    # Plot & Save Confusion Matrix Image
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=LABEL_NAMES, yticklabels=LABEL_NAMES)
    plt.title(f"Confusion Matrix — Round 2 ({arch} | {strategy})")
    plt.xlabel("Predicted DR Grade")
    plt.ylabel("True DR Grade")
    plt.tight_layout()

    cm_img_path = os.path.join(reports_dir, "confusion_matrix.png")
    plt.savefig(cm_img_path, dpi=300)
    plt.close()

    print(f"Round 2 Evaluation complete!")
    print(f"Strategy: {strategy}")
    print(f"Accuracy: {accuracy:.4f} | Macro F1: {macro_f1:.4f} | Weighted F1: {weighted_f1:.4f}")
    print(f"Confusion matrix plot saved to {cm_img_path}")
    return test_metrics

if __name__ == "__main__":
    evaluate_model()
