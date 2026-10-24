import os
import sys
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BASE_DIR = os.path.join(PROJECT_ROOT, "data", "PlantVillage")

def find_dataset_path(base_dir):
    if not os.path.exists(base_dir):
        return base_dir
    for root, dirs, files in os.walk(base_dir):
        disease_dirs = [d for d in dirs if "___" in d]
        if disease_dirs:
            return root
    return base_dir

DATASET_PATH = find_dataset_path(BASE_DIR)

data = []
for class_name in sorted(os.listdir(DATASET_PATH)):
    class_path = os.path.join(DATASET_PATH, class_name)
    if not os.path.isdir(class_path):
        continue
    images = [
        file for file in os.listdir(class_path)
        if file.lower().endswith((".jpg", ".jpeg", ".png"))
    ]
    parts = class_name.split("___")
    crop = parts[0]
    disease = parts[1] if len(parts) > 1 else "Unknown"
    data.append({
        "Crop": crop,
        "Disease": disease,
        "Class_Name": class_name,
        "Images": len(images)
    })

df = pd.DataFrame(data)
print(df.to_string())

output_csv = os.path.join(PROJECT_ROOT, "data", "dataset_report.csv")
df.to_csv(output_csv, index=False)
print(f"\nDataset report created successfully at {output_csv}.")
