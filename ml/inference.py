import os
import time
import json
from PIL import Image

import torch
import torch.nn as nn
from torchvision import transforms, models

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
MODEL_DIR = os.path.join(PROJECT_ROOT, "backend", "model")
WEIGHTS_PATH = os.path.join(MODEL_DIR, "plant_disease_model.pth")
CLASS_INFO_PATH = os.path.join(MODEL_DIR, "class_indices.json")
DISEASE_DB_PATH = os.path.join(PROJECT_ROOT, "backend", "app", "data", "disease_info.json")

class PlantDiseasePredictor:
    def __init__(self, weights_path=WEIGHTS_PATH, class_info_path=CLASS_INFO_PATH, disease_db_path=DISEASE_DB_PATH):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.weights_path = weights_path
        self.class_info_path = class_info_path
        self.disease_db_path = disease_db_path
        
        self.classes = []
        self.class_to_idx = {}
        self.idx_to_class = {}
        self.disease_db = {}
        self.model = None
        
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        self._load_metadata()
        self._load_model()
        
    def _load_metadata(self):
        if os.path.exists(self.class_info_path):
            with open(self.class_info_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.classes = data["classes"]
                self.class_to_idx = data["class_to_idx"]
                self.idx_to_class = {int(k): v for k, v in data["idx_to_class"].items()}
                
        if os.path.exists(self.disease_db_path):
            with open(self.disease_db_path, "r", encoding="utf-8") as f:
                self.disease_db = json.load(f)
                
    def _load_model(self):
        if not os.path.exists(self.weights_path) or not self.classes:
            return
            
        num_classes = len(self.classes)
        model = models.mobilenet_v3_small(weights=None)
        in_features = model.classifier[3].in_features
        model.classifier[3] = nn.Sequential(
            nn.Dropout(p=0.2),
            nn.Linear(in_features, num_classes)
        )
        model.load_state_dict(torch.load(self.weights_path, map_location=self.device))
        model.to(self.device)
        model.eval()
        self.model = model
        print("PlantDiseasePredictor loaded successfully.")

    def is_ready(self):
        return self.model is not None

    def predict(self, image_input, top_k=3):
        if not self.is_ready():
            self._load_metadata()
            self._load_model()
            if not self.is_ready():
                raise RuntimeError("Model weights not yet loaded or model is still training.")
                
        if isinstance(image_input, str):
            image = Image.open(image_input).convert("RGB")
        elif isinstance(image_input, bytes):
            import io
            image = Image.open(io.BytesIO(image_input)).convert("RGB")
        elif isinstance(image_input, Image.Image):
            image = image_input.convert("RGB")
        else:
            raise ValueError("Unsupported image input format.")
            
        tensor = self.transform(image).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(tensor)
            probabilities = torch.softmax(outputs, dim=1)[0]
            
        top_probs, top_indices = torch.topk(probabilities, k=min(top_k, len(self.classes)))
        
        predictions = []
        for prob, idx in zip(top_probs.tolist(), top_indices.tolist()):
            class_name = self.idx_to_class.get(idx, self.classes[idx])
            info = self.disease_db.get(class_name, {
                "crop": class_name.split("___")[0],
                "common_name": class_name.replace("___", " - ").replace("_", " "),
                "status": "Healthy" if "healthy" in class_name.lower() else "Diseased",
                "pathogen_type": "Unknown",
                "severity": "Unknown",
                "description": "Details unavailable.",
                "symptoms": [],
                "organic_treatment": [],
                "chemical_treatment": [],
                "prevention": []
            })
            
            predictions.append({
                "class_name": class_name,
                "confidence": round(prob * 100, 2),
                "crop": info.get("crop"),
                "common_name": info.get("common_name"),
                "status": info.get("status"),
                "pathogen_type": info.get("pathogen_type"),
                "severity": info.get("severity"),
                "description": info.get("description"),
                "symptoms": info.get("symptoms", []),
                "organic_treatment": info.get("organic_treatment", []),
                "chemical_treatment": info.get("chemical_treatment", []),
                "prevention": info.get("prevention", [])
            })
            
        primary = predictions[0]
        alternates = predictions[1:]
        
        return {
            "primary": primary,
            "alternates": alternates,
            "device": str(self.device),
            "timestamp": time.time()
        }

if __name__ == "__main__":
    import time
    predictor = PlantDiseasePredictor()
    test_img = os.path.join(PROJECT_ROOT, "backend", "app", "static", "samples", "tomato_early_blight.jpg")
    if os.path.exists(test_img) and predictor.is_ready():
        res = predictor.predict(test_img)
        print("Prediction on sample:")
        print(f"Top 1: {res['primary']['common_name']} ({res['primary']['confidence']}%)")
    else:
        print("Predictor ready:", predictor.is_ready())
