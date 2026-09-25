import os
import json
import pandas as pd
import numpy as np
from PIL import Image
from sklearn.model_selection import train_test_split

DEFAULT_MESSIDOR_DIR = "/Users/sakshishetty/.cache/kagglehub/datasets/mariaherrerot/messidor2preprocess/versions/2"
MESSIDOR_DATA_DIR = os.environ.get("DATASET_DIR", DEFAULT_MESSIDOR_DIR)
CSV_PATH = os.path.join(MESSIDOR_DATA_DIR, "messidor_data.csv")

LABEL_MAPPING = {
    0: "No DR",
    1: "Mild NPDR",
    2: "Moderate NPDR",
    3: "Severe NPDR",
    4: "Proliferative DR"
}

def inspect_and_prepare_dataset(output_dir="ml"):
    os.makedirs(os.path.join(output_dir, "reports"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "data_splits"), exist_ok=True)
    
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"Messidor-2 CSV not found at {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)
    
    # Locate all image files in dataset directory
    img_map = {}
    for root, dirs, files in os.walk(MESSIDOR_DATA_DIR):
        for f in files:
            if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                img_map[f] = os.path.join(root, f)

    df["full_image_path"] = df["id_code"].map(img_map)
    
    total_records = int(len(df))
    matched_records = int(df["full_image_path"].notna().sum())
    
    valid_df = df[df["full_image_path"].notna()].copy()
    
    corrupted_count = 0
    dimensions = []
    
    for idx, row in valid_df.iterrows():
        try:
            with Image.open(row["full_image_path"]) as img:
                dimensions.append(img.size) # (width, height)
        except Exception:
            corrupted_count += 1
            
    usable_count = matched_records - corrupted_count
    
    class_counts = valid_df["diagnosis"].value_counts().sort_index().to_dict()
    class_distribution = {
        str(int(cls)): {
            "name": LABEL_MAPPING.get(int(cls), f"Class {cls}"),
            "count": int(count),
            "percentage": round(float((count / len(valid_df)) * 100), 2)
        }
        for cls, count in class_counts.items()
    }

    dim_series = pd.Series([f"{w}x{h}" for w, h in dimensions])
    unique_dimensions = {str(k): int(v) for k, v in dim_series.value_counts().to_dict().items()}

    dataset_report = {
        "dataset_name": "MESSIDOR-2 Preprocessed",
        "total_records": total_records,
        "matched_images": matched_records,
        "usable_images": usable_count,
        "corrupted_images": corrupted_count,
        "duplicate_images": int(valid_df["id_code"].duplicated().sum()),
        "image_dimensions_distribution": unique_dimensions,
        "class_counts": {str(int(k)): int(v) for k, v in class_counts.items()},
        "class_distribution": class_distribution
    }

    # Save JSON report
    report_json_path = os.path.join(output_dir, "reports", "dataset_report.json")
    with open(report_json_path, "w") as f:
        json.dump(dataset_report, f, indent=2)

    # Save Markdown report
    report_md_path = os.path.join(output_dir, "reports", "dataset_report.md")
    with open(report_md_path, "w") as f:
        f.write("# MESSIDOR-2 Dataset Report\n\n")
        f.write(f"- **Dataset Name**: {dataset_report['dataset_name']}\n")
        f.write(f"- **Total CSV Records**: {dataset_report['total_records']}\n")
        f.write(f"- **Usable Images**: {dataset_report['usable_images']}\n")
        f.write(f"- **Corrupted Images**: {dataset_report['corrupted_images']}\n")
        f.write(f"- **Duplicate Images**: {dataset_report['duplicate_images']}\n")
        f.write(f"- **Image Resolutions**: {dataset_report['image_dimensions_distribution']}\n\n")
        f.write("### DR Severity Class Distribution\n\n")
        f.write("| Grade | Class Name | Count | Percentage |\n")
        f.write("|---|---|---|---|\n")
        for k, v in class_distribution.items():
            f.write(f"| {k} | {v['name']} | {v['count']} | {v['percentage']}% |\n")

    print(f"Dataset report written to {report_json_path} and {report_md_path}")

    # Perform Stratified Train / Val / Test Split (70% / 15% / 15%)
    # Seed 42 for 100% reproducibility
    train_df, test_val_df = train_test_split(
        valid_df,
        test_size=0.30,
        random_state=42,
        stratify=valid_df["diagnosis"]
    )
    
    val_df, test_df = train_test_split(
        test_val_df,
        test_size=0.50,
        random_state=42,
        stratify=test_val_df["diagnosis"]
    )
    
    train_path = os.path.join(output_dir, "data_splits", "train.csv")
    val_path = os.path.join(output_dir, "data_splits", "validation.csv")
    test_path = os.path.join(output_dir, "data_splits", "test.csv")

    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)

    print(f"Splits saved: Train ({len(train_df)}), Validation ({len(val_df)}), Test ({len(test_df)})")
    return dataset_report

if __name__ == "__main__":
    inspect_and_prepare_dataset()
