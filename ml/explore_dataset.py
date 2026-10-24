import os
import sys
import matplotlib.pyplot as plt
from PIL import Image

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

classes = [
    "Tomato___healthy",
    "Tomato___Early_blight",
    "Tomato___Late_blight"
]

fig, axes = plt.subplots(1, 3, figsize=(12, 4))

for i, class_name in enumerate(classes):
    class_path = os.path.join(DATASET_PATH, class_name)
    if os.path.exists(class_path):
        images = [
            file for file in os.listdir(class_path)
            if file.lower().endswith((".jpg", ".jpeg", ".png"))
        ]
        if images:
            image_path = os.path.join(class_path, images[0])
            image = Image.open(image_path)
            axes[i].imshow(image)
            axes[i].set_title(class_name)
            axes[i].axis("off")
        else:
            axes[i].set_title(f"{class_name}\n(No images)")
            axes[i].axis("off")
    else:
        axes[i].set_title(f"{class_name}\n(Not found)")
        axes[i].axis("off")

plt.tight_layout()
output_img = os.path.join(PROJECT_ROOT, "data", "sample_images.png")
plt.savefig(output_img)
print(f"Sample visualization saved to {output_img}")
plt.close()
