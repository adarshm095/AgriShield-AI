import os
import json
import io
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Body, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from app.predictor import get_predictor
from app.db.mongo import mongo_manager

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
STATIC_DIR = os.path.join(SCRIPT_DIR, "static")
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
DISEASE_DB_PATH = os.path.join(SCRIPT_DIR, "data", "disease_info.json")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect to MongoDB on startup
    await mongo_manager.connect()
    yield

app = FastAPI(
    title="AgriShield-AI API",
    description="Intelligent Crop Disease Diagnosis & Agronomic Protection with MongoDB Database Integration",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

def load_fallback_disease_db():
    if os.path.exists(DISEASE_DB_PATH):
        with open(DISEASE_DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# ============================================================
# Health & MongoDB Database Status Endpoints
# ============================================================

@app.get("/api/health")
async def health_check():
    predictor = get_predictor()
    mongo_status = await mongo_manager.get_status()
    return {
        "status": "online",
        "service": "AgriShield-AI",
        "version": "2.0.0",
        "model_loaded": predictor.is_ready(),
        "device": str(predictor.device),
        "total_classes": len(predictor.classes),
        "mongodb": mongo_status
    }

@app.get("/api/db/status")
async def get_db_status():
    """Returns MongoDB Atlas / Compass connection details and live collection document counts"""
    return await mongo_manager.get_status()

@app.post("/api/db/seed")
async def seed_mongodb(force: bool = False):
    """Seed or update all 38 diseases in MongoDB"""
    count = await mongo_manager.seed_diseases(force=force)
    return {"status": "success", "seeded_diseases": count}

# ============================================================
# Farms & Observations Endpoints (MongoDB)
# ============================================================

@app.get("/api/farms")
async def get_farms():
    """Retrieve list of registered farms from MongoDB"""
    farms = await mongo_manager.get_farms()
    return {"total": len(farms), "farms": farms}

@app.get("/api/observations")
async def get_observations(limit: int = 50):
    """Retrieve scan observations stored in MongoDB 'crop_observations' collection"""
    observations = await mongo_manager.get_observations(limit=limit)
    return {"total": len(observations), "observations": observations}

@app.delete("/api/observations/{obs_id}")
async def delete_observation(obs_id: str):
    """Delete an observation from MongoDB"""
    success = await mongo_manager.delete_observation(obs_id)
    if not success:
        raise HTTPException(status_code=404, detail="Observation not found or could not be deleted.")
    return {"status": "deleted", "id": obs_id}

# ============================================================
# Prediction Endpoints (Auto-logged to MongoDB)
# ============================================================

@app.post("/api/predict")
async def predict_leaf_disease(
    file: UploadFile = File(...),
    farm_id: Optional[str] = Form(None),
    farmer_name: Optional[str] = Form(None)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.")
    
    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Empty image payload received.")
    
    predictor = get_predictor()
    try:
        results = predictor.predict(contents, top_k=3)
        results["filename"] = file.filename
        
        # Save diagnosis into MongoDB 'crop_observations'
        obs_record = await mongo_manager.save_observation(
            prediction_data=results,
            farm_id=farm_id,
            farmer_name=farmer_name,
            image_url=f"/static/uploads/{file.filename}"
        )
        if obs_record:
            results["observation_id"] = obs_record.get("_id")
            results["mongo_saved"] = True
            results["farm_id"] = obs_record.get("farmId")
            results["farmer_name"] = obs_record.get("farmerName")
            results["risk_level"] = obs_record.get("riskLevel")
        else:
            results["mongo_saved"] = False
            
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

@app.post("/api/predict-sample/{sample_id}")
async def predict_sample(
    sample_id: str,
    farm_id: Optional[str] = Query(None),
    farmer_name: Optional[str] = Query(None)
):
    samples_manifest_path = os.path.join(STATIC_DIR, "samples", "samples.json")
    if not os.path.exists(samples_manifest_path):
        raise HTTPException(status_code=404, detail="Samples catalog not found.")
        
    with open(samples_manifest_path, "r", encoding="utf-8") as f:
        samples = json.load(f)
        
    matched = next((s for s in samples if s["id"] == sample_id or s["filename"] == sample_id), None)
    if not matched:
        raise HTTPException(status_code=404, detail=f"Sample '{sample_id}' not found.")
        
    img_path = os.path.join(STATIC_DIR, "samples", matched["filename"])
    if not os.path.exists(img_path):
        raise HTTPException(status_code=404, detail="Sample image file missing on disk.")
        
    predictor = get_predictor()
    try:
        results = predictor.predict(img_path, top_k=3)
        results["sample_info"] = matched
        results["filename"] = matched["filename"]
        
        # Log to MongoDB 'crop_observations'
        obs_record = await mongo_manager.save_observation(
            prediction_data=results,
            farm_id=farm_id,
            farmer_name=farmer_name,
            image_url=matched["url"]
        )
        if obs_record:
            results["observation_id"] = obs_record.get("_id")
            results["mongo_saved"] = True
            results["farm_id"] = obs_record.get("farmId")
            results["farmer_name"] = obs_record.get("farmerName")
            results["risk_level"] = obs_record.get("riskLevel")
        else:
            results["mongo_saved"] = False
            
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

# ============================================================
# Diseases & Crops Catalog Endpoints
# ============================================================

@app.get("/api/diseases")
async def get_diseases(
    crop: Optional[str] = Query(None, description="Filter by crop name (e.g. Tomato, Apple)"),
    status: Optional[str] = Query(None, description="Filter by status (Healthy or Diseased)"),
    pathogen: Optional[str] = Query(None, description="Filter by pathogen type")
):
    # Try fetching from MongoDB first
    if mongo_manager.is_connected:
        items = await mongo_manager.get_diseases(crop=crop, status=status, pathogen=pathogen)
        if items:
            return {"total": len(items), "source": "mongodb", "diseases": items}
            
    # Fallback to local JSON
    db = load_fallback_disease_db()
    items = []
    for class_name, details in db.items():
        if crop and details.get("crop", "").lower() != crop.lower():
            continue
        if status and details.get("status", "").lower() != status.lower():
            continue
        if pathogen and details.get("pathogen_type", "").lower() != pathogen.lower():
            continue
        item = {"class_name": class_name, **details}
        items.append(item)
    return {"total": len(items), "source": "local_cache", "diseases": items}

@app.get("/api/diseases/{class_name}")
async def get_disease_detail(class_name: str):
    if mongo_manager.is_connected and mongo_manager.db is not None:
        doc = await mongo_manager.db.diseases.find_one({"$or": [{"class_name": class_name}, {"name": class_name}]})
        if doc:
            doc["id"] = str(doc.pop("_id"))
            return doc
            
    db = load_fallback_disease_db()
    if class_name not in db:
        raise HTTPException(status_code=404, detail=f"Disease class '{class_name}' not found.")
    return {"class_name": class_name, **db[class_name]}

@app.get("/api/crops")
async def get_crops():
    crops_map = {}
    if mongo_manager.is_connected and mongo_manager.db is not None:
        cursor = mongo_manager.db.diseases.find({})
        async for doc in cursor:
            crop_name = doc.get("crop", "Unknown")
            if crop_name not in crops_map:
                crops_map[crop_name] = {"crop": crop_name, "conditions_count": 0, "classes": []}
            crops_map[crop_name]["conditions_count"] += 1
            crops_map[crop_name]["classes"].append({
                "name": doc.get("name", doc.get("common_name")),
                "status": doc.get("status")
            })
        if crops_map:
            return {"total_crops": len(crops_map), "source": "mongodb", "crops": list(crops_map.values())}

    db = load_fallback_disease_db()
    for class_name, details in db.items():
        crop_name = details.get("crop", "Unknown")
        if crop_name not in crops_map:
            crops_map[crop_name] = {"crop": crop_name, "conditions_count": 0, "classes": []}
        crops_map[crop_name]["conditions_count"] += 1
        crops_map[crop_name]["classes"].append({
            "class_name": class_name,
            "common_name": details.get("common_name"),
            "status": details.get("status")
        })
    return {"total_crops": len(crops_map), "source": "local_cache", "crops": list(crops_map.values())}

@app.get("/api/samples")
def get_sample_images():
    samples_manifest_path = os.path.join(STATIC_DIR, "samples", "samples.json")
    if os.path.exists(samples_manifest_path):
        with open(samples_manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# ============================================================
# Frontend SPA Static Serving
# ============================================================

if os.path.exists(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets") if os.path.exists(os.path.join(FRONTEND_DIR, "assets")) else FRONTEND_DIR), name="assets")

@app.get("/")
def serve_index():
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "AgriShield-AI API is running. Access OpenAPI docs at /docs."}

@app.get("/{full_path:path}")
def serve_frontend_spa(full_path: str):
    if full_path.startswith("api/") or full_path.startswith("static/"):
        raise HTTPException(status_code=404, detail="Not Found")
    requested = os.path.join(FRONTEND_DIR, full_path)
    if os.path.exists(requested) and os.path.isfile(requested):
        return FileResponse(requested)
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    raise HTTPException(status_code=404, detail="Not Found")
