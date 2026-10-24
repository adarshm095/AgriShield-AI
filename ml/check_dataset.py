import os
import sys

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

print("Checking dataset...")
print(f"Resolved Dataset Path: {DATASET_PATH}")

if not os.path.exists(DATASET_PATH):
    print("Dataset folder not found!")
    exit()

print("Dataset found!\n")

total_images = 0
print("Disease Classes:\n")

for class_name in sorted(os.listdir(DATASET_PATH)):
    class_path = os.path.join(DATASET_PATH, class_name)
    if os.path.isdir(class_path):
        images = [
            file for file in os.listdir(class_path)
            if file.lower().endswith((".jpg", ".jpeg", ".png"))
        ]
        print(f"{class_name}: {len(images)} images")
        total_images += len(images)

print("\nTotal images:", total_images)
