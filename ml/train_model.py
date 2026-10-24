import os
import sys
import time
import json
import random
from PIL import Image

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models

# Set seed for reproducibility
random.seed(42)
torch.manual_seed(42)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATASET_PATH = os.path.join(PROJECT_ROOT, "data", "PlantVillage", "raw", "color")
MODEL_DIR = os.path.join(PROJECT_ROOT, "backend", "model")
os.makedirs(MODEL_DIR, exist_ok=True)

class PlantVillageDataset(Dataset):
    def __init__(self, samples, transform=None):
        self.samples = samples
        self.transform = transform

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        try:
            image = Image.open(path).convert("RGB")
        except Exception:
            image = Image.new("RGB", (224, 224), (0, 0, 0))
        if self.transform:
            image = self.transform(image)
        return image, label

def prepare_data(dataset_path, train_per_class=60, val_per_class=15, test_per_class=10):
    classes = sorted([d for d in os.listdir(dataset_path) if os.path.isdir(os.path.join(dataset_path, d))])
    class_to_idx = {cls_name: idx for idx, cls_name in enumerate(classes)}
    
    train_samples = []
    val_samples = []
    test_samples = []
    
    for cls_name in classes:
        cls_dir = os.path.join(dataset_path, cls_name)
        img_files = [
            os.path.join(cls_dir, f)
            for f in os.listdir(cls_dir)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        ]
        random.shuffle(img_files)
        
        n_train = min(train_per_class, int(len(img_files) * 0.7))
        n_val = min(val_per_class, int(len(img_files) * 0.15))
        n_test = min(test_per_class, len(img_files) - n_train - n_val)
        
        for f in img_files[:n_train]:
            train_samples.append((f, class_to_idx[cls_name]))
        for f in img_files[n_train:n_train+n_val]:
            val_samples.append((f, class_to_idx[cls_name]))
        for f in img_files[n_train+n_val:n_train+n_val+n_test]:
            test_samples.append((f, class_to_idx[cls_name]))
            
    print(f"Loaded {len(classes)} classes.")
    print(f"Total split -> Train: {len(train_samples)}, Val: {len(val_samples)}, Test: {len(test_samples)}")
    return classes, class_to_idx, train_samples, val_samples, test_samples

def get_transforms():
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.1, contrast=0.1),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    eval_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    return train_transform, eval_transform

def build_model(num_classes):
    print("Initializing MobileNetV3-Small architecture with pretrained weights...")
    weights = models.MobileNet_V3_Small_Weights.DEFAULT
    model = models.mobilenet_v3_small(weights=weights)
    
    # Freeze initial feature layers for quick transfer learning
    for param in model.features[:-3].parameters():
        param.requires_grad = False
        
    in_features = model.classifier[3].in_features
    model.classifier[3] = nn.Sequential(
        nn.Dropout(p=0.2),
        nn.Linear(in_features, num_classes)
    )
    return model

def train_epoch(model, loader, criterion, optimizer, device):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item() * images.size(0)
        _, preds = torch.max(outputs, 1)
        correct += (preds == labels).sum().item()
        total += labels.size(0)
        
    return running_loss / total, correct / total

def eval_epoch(model, loader, criterion, device):
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    
    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)
            
            running_loss += loss.item() * images.size(0)
            _, preds = torch.max(outputs, 1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)
            
    return running_loss / total, correct / total

def main():
    start_time = time.time()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on device: {device}")
    
    classes, class_to_idx, train_samples, val_samples, test_samples = prepare_data(
        DATASET_PATH, train_per_class=50, val_per_class=12, test_per_class=8
    )
    
    # Save class indices
    idx_to_class = {v: k for k, v in class_to_idx.items()}
    class_info = {
        "classes": classes,
        "class_to_idx": class_to_idx,
        "idx_to_class": idx_to_class,
        "num_classes": len(classes)
    }
    with open(os.path.join(MODEL_DIR, "class_indices.json"), "w", encoding="utf-8") as f:
        json.dump(class_info, f, indent=2)
    print("Saved class_indices.json")
    
    train_transform, eval_transform = get_transforms()
    train_dataset = PlantVillageDataset(train_samples, transform=train_transform)
    val_dataset = PlantVillageDataset(val_samples, transform=eval_transform)
    test_dataset = PlantVillageDataset(test_samples, transform=eval_transform)
    
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False, num_workers=0)
    
    model = build_model(len(classes)).to(device)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.05)
    optimizer = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad],
        lr=0.001,
        weight_decay=1e-4
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=4)
    
    num_epochs = 4
    best_val_acc = 0.0
    best_weights_path = os.path.join(MODEL_DIR, "plant_disease_model.pth")
    
    print("\n--- Starting Training ---")
    for epoch in range(1, num_epochs + 1):
        epoch_start = time.time()
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc = eval_epoch(model, val_loader, criterion, device)
        scheduler.step()
        epoch_dur = time.time() - epoch_start
        
        print(f"Epoch [{epoch}/{num_epochs}] ({epoch_dur:.1f}s) - "
              f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc*100:.2f}% | "
              f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc*100:.2f}%")
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), best_weights_path)
            print(f"  -> Best model saved with Val Acc: {val_acc*100:.2f}%")
            
    # Final evaluation on held-out test set
    print("\n--- Evaluating on Test Set ---")
    model.load_state_dict(torch.load(best_weights_path, map_location=device))
    test_loss, test_acc = eval_epoch(model, test_loader, criterion, device)
    print(f"Final Test Loss: {test_loss:.4f}, Test Accuracy: {test_acc*100:.2f}%")
    
    elapsed = time.time() - start_time
    print(f"Training and evaluation completed successfully in {elapsed:.1f} seconds.")

if __name__ == "__main__":
    main()
