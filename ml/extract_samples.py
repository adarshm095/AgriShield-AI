import os
import shutil

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_PATH = os.path.join(PROJECT_ROOT, "data", "PlantVillage", "raw", "color")

SAMPLE_CLASSES = [
    ("Tomato___Early_blight", "tomato_early_blight.jpg", "Tomato Early Blight"),
    ("Tomato___Late_blight", "tomato_late_blight.jpg", "Tomato Late Blight"),
    ("Tomato___healthy", "tomato_healthy.jpg", "Tomato Healthy"),
    ("Apple___Apple_scab", "apple_scab.jpg", "Apple Scab"),
    ("Corn_(maize)___Common_rust_", "corn_common_rust.jpg", "Corn Common Rust"),
    ("Grape___Black_rot", "grape_black_rot.jpg", "Grape Black Rot"),
    ("Orange___Haunglongbing_(Citrus_greening)", "citrus_greening.jpg", "Citrus Greening"),
    ("Potato___Late_blight", "potato_late_blight.jpg", "Potato Late Blight"),
    ("Pepper,_bell___Bacterial_spot", "pepper_bacterial_spot.jpg", "Pepper Bacterial Spot"),
    ("Strawberry___Leaf_scorch", "strawberry_leaf_scorch.jpg", "Strawberry Leaf Scorch")
]

def copy_samples():
    dst_dir = os.path.join(PROJECT_ROOT, "backend", "app", "static", "samples")
    os.makedirs(dst_dir, exist_ok=True)
    
    samples_manifest = []
    
    for class_name, out_filename, title in SAMPLE_CLASSES:
        src_folder = os.path.join(DATASET_PATH, class_name)
        if not os.path.exists(src_folder):
            continue
        images = [f for f in os.listdir(src_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if not images:
            continue
        
        # Pick the second or third image to avoid any edge artifacts
        chosen_img = images[min(2, len(images)-1)]
        src_path = os.path.join(src_folder, chosen_img)
        dst_path = os.path.join(dst_dir, out_filename)
        shutil.copyfile(src_path, dst_path)
        print(f"Copied {class_name} sample -> {dst_path}")
        
        samples_manifest.append({
            "id": out_filename.replace(".jpg", ""),
            "title": title,
            "class_name": class_name,
            "filename": out_filename,
            "url": f"/static/samples/{out_filename}"
        })
        
    import json
    manifest_path = os.path.join(dst_dir, "samples.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(samples_manifest, f, indent=2)
    print(f"Saved samples manifest to {manifest_path}")

if __name__ == "__main__":
    copy_samples()
