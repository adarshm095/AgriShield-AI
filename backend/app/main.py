import os
import json
import io
import httpx
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Body, Form, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

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
    description="Farmer-Centric Crop Health & Disease Diagnostics with Dynamic Field Management",
    version="2.1.0",
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
os.makedirs(os.path.join(STATIC_DIR, "uploads"), exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

def load_fallback_disease_db():
    if os.path.exists(DISEASE_DB_PATH):
        with open(DISEASE_DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# ============================================================
# Pydantic Request Models
# ============================================================

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2)
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=4)
    phone: Optional[str] = None
    role: Optional[str] = "Farmer"
    location: Optional[str] = ""

class LoginRequest(BaseModel):
    identifier: str = Field(..., min_length=2)
    password: str = Field(..., min_length=1)

class FarmCreateRequest(BaseModel):
    farmName: str = Field(..., min_length=2)
    crop: str = Field(..., min_length=2)
    area: Optional[float] = 1.0
    location: Optional[str] = "Local Field"
    sowingDate: Optional[str] = None
    farmerId: Optional[str] = None
    farmerName: Optional[str] = None

class AdvisorQueryRequest(BaseModel):
    question: str
    crop: Optional[str] = "Crop"
    disease: Optional[str] = "Leaf condition"
    severity: Optional[str] = "Moderate"
    language: Optional[str] = "en"

# ============================================================
# Authentication Endpoints
# ============================================================

@app.post("/api/auth/register")
async def register_farmer(req: RegisterRequest):
    """Register a new farmer account and initialize their workspace"""
    try:
        result = await mongo_manager.register_user(
            name=req.name,
            email=req.email,
            password=req.password,
            phone=req.phone,
            role=req.role or "Farmer",
            location=req.location or ""
        )
        return {"status": "success", "token": result["token"], "user": result["user"]}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/api/auth/login")
async def login_farmer(req: LoginRequest):
    """Authenticate farmer with email or phone number"""
    try:
        result = await mongo_manager.login_user(
            identifier=req.identifier,
            password=req.password
        )
        return {"status": "success", "token": result["token"], "user": result["user"]}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.get("/api/auth/me")
async def get_current_user(authorization: Optional[str] = Header(None), token: Optional[str] = Query(None)):
    """Retrieve profile of currently authenticated farmer"""
    auth_token = None
    if authorization and authorization.startswith("Bearer "):
        auth_token = authorization.split("Bearer ")[1].strip()
    elif token:
        auth_token = token

    if not auth_token:
        raise HTTPException(status_code=401, detail="Authentication token required.")

    user = await mongo_manager.get_user_by_token(auth_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session token.")
    return {"status": "success", "user": user}

# ============================================================
# Dynamic Farms & Crop Fields
# ============================================================

@app.get("/api/farms")
async def get_farms(farmer_id: Optional[str] = Query(None)):
    """Retrieve registered crop fields, dynamically filtered by farmer"""
    farms = await mongo_manager.get_farms(farmer_id=farmer_id)
    return {"total": len(farms), "farms": farms}

@app.post("/api/farms")
async def create_farm(farm: FarmCreateRequest):
    """Add a new custom farm/field plot to the system"""
    created = await mongo_manager.create_farm(farm.model_dump())
    return {"status": "success", "farm": created}

# ============================================================
# Health & Clean Database Status Endpoints
# ============================================================

@app.get("/api/health")
async def health_check():
    predictor = get_predictor()
    mongo_status = await mongo_manager.get_status()
    return {
        "status": "online",
        "service": "AgriShield-AI",
        "version": "2.1.0",
        "model_loaded": predictor.is_ready(),
        "device": str(predictor.device),
        "total_classes": len(predictor.classes),
        "database": {
            "status": mongo_status.get("status", "Online"),
            "connected": mongo_status.get("connected", False)
        },
        "mongodb": mongo_status
    }

@app.get("/api/db/status")
async def get_db_status():
    """Returns safe database metrics without exposing raw connection strings"""
    return await mongo_manager.get_status()

@app.post("/api/db/seed")
async def seed_mongodb(force: bool = False):
    """Sync disease encyclopedia in database"""
    count = await mongo_manager.seed_diseases(force=force)
    return {"status": "success", "seeded_diseases": count}

# ============================================================
# Observations & Past Scans
# ============================================================

@app.get("/api/observations")
async def get_observations(farmer_id: Optional[str] = Query(None), limit: int = 50):
    """Retrieve scan history for the farmer"""
    observations = await mongo_manager.get_observations(farmer_id=farmer_id, limit=limit)
    return {"total": len(observations), "observations": observations}

@app.delete("/api/observations/{obs_id}")
async def delete_observation(obs_id: str):
    """Delete a past scan observation"""
    success = await mongo_manager.delete_observation(obs_id)
    if not success:
        raise HTTPException(status_code=404, detail="Observation not found.")
    return {"status": "deleted", "id": obs_id}

# ============================================================
# Leaf Disease Prediction Endpoints
# ============================================================

@app.post("/api/predict")
async def predict_leaf_disease(
    file: UploadFile = File(...),
    farm_id: Optional[str] = Form(None),
    farmer_name: Optional[str] = Form(None),
    farmer_id: Optional[str] = Form(None)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a valid image.")
    
    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Empty image payload received.")
    
    # Save uploaded file locally for viewing
    safe_filename = f"upload_{file.filename.replace(' ', '_')}"
    upload_path = os.path.join(STATIC_DIR, "uploads", safe_filename)
    try:
        with open(upload_path, "wb") as f:
            f.write(contents)
        image_url = f"/static/uploads/{safe_filename}"
    except Exception:
        image_url = f"/static/samples/leaf.jpg"

    predictor = get_predictor()
    try:
        results = predictor.predict(contents, top_k=3)
        results["filename"] = file.filename
        
        # Save diagnosis into persistent observation record
        obs_record = await mongo_manager.save_observation(
            prediction_data=results,
            farm_id=farm_id,
            farmer_name=farmer_name,
            farmer_id=farmer_id,
            image_url=image_url
        )
        if obs_record:
            results["observation_id"] = obs_record.get("id") or obs_record.get("_id")
            results["mongo_saved"] = True
            results["farm_id"] = obs_record.get("farmId")
            results["farmer_name"] = obs_record.get("farmerName")
            results["farmer_id"] = obs_record.get("farmerId")
            results["risk_level"] = obs_record.get("riskLevel")
        else:
            results["mongo_saved"] = False
            
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnostic analysis error: {str(e)}")

@app.post("/api/predict-sample/{sample_id}")
async def predict_sample(
    sample_id: str,
    farm_id: Optional[str] = Query(None),
    farmer_name: Optional[str] = Query(None),
    farmer_id: Optional[str] = Query(None)
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
        
        obs_record = await mongo_manager.save_observation(
            prediction_data=results,
            farm_id=farm_id,
            farmer_name=farmer_name,
            farmer_id=farmer_id,
            image_url=matched["url"]
        )
        if obs_record:
            results["observation_id"] = obs_record.get("id") or obs_record.get("_id")
            results["mongo_saved"] = True
            results["farm_id"] = obs_record.get("farmId")
            results["farmer_name"] = obs_record.get("farmerName")
            results["farmer_id"] = obs_record.get("farmerId")
            results["risk_level"] = obs_record.get("riskLevel")
        else:
            results["mongo_saved"] = False
            
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnostic analysis error: {str(e)}")

# ============================================================
# Interactive AI Agronomist Copilot (LLM Advisory Endpoint)
# ============================================================

@app.post("/api/ai/advisor")
async def ask_agri_advisor(req: AdvisorQueryRequest):
    """
    Interactive Agronomist Assistant:
    Provides conversational, practical crop protection answers.
    Supports English & Hindi.
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    q = req.question.lower()
    is_hindi = (req.language or "en").lower() == "hi"

    # If GEMINI_API_KEY is available, we query Google Gemini LLM
    if gemini_key:
        try:
            prompt = (
                f"You are AgriShield AI Agronomist, a friendly, practical crop doctor advising Indian farmers. "
                f"Crop: {req.crop}. Disease: {req.disease}. Severity: {req.severity}. "
                f"Farmer Question: {req.question}. "
                f"Language required: {'Hindi (conversational Devnagari script)' if is_hindi else 'Simple, practical English'}. "
                f"Keep your response concise, actionable, giving exact doses, organic tips, and precautions. Avoid jargon."
            )
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    answer = data["candidates"][0]["content"]["parts"][0]["text"]
                    return {"status": "success", "answer": answer, "engine": "Gemini LLM"}
        except Exception as e:
            pass  # Fallback to local intelligent advisory engine

    # Resilient Agricultural Advisory Engine
    if is_hindi:
        if "organic" in q or "desi" in q or "neem" in q or "जैविक" in q or "देसी" in q:
            advice = (
                f"🌿 **{req.crop} के लिए जैविक उपचार (Organic Remedy):**\n\n"
                f"1. **नीम तेल स्प्रे:** 1 लीटर पानी में 5 मिली नीम का तेल और 1 मिली शैम्पू मिलाकर शाम 5 बजे के बाद छिड़काव करें।\n"
                f"2. **छाछ और हींग का घोल:** 5 लीटर खट्टी छाछ को 15 लीटर पानी में मिलाकर पत्तियों पर स्प्रे करें (फंगल और ब्लाइट में बहुत असरदार)।\n"
                f"3. संक्रमित पत्तियों को तोड़कर खेत से दूर गड्ढे में दबाएं ताकि यह रोग बाकी पौधों में न फैले।"
            )
        elif "spray" in q or "dawa" in q or "chemical" in q or "दवा" in q or "स्प्रे" in q:
            advice = (
                f"🧪 **{req.crop} ({req.disease}) के लिए रासायनिक दवा छिड़काव गाइड:**\n\n"
                f"1. **दवा का नाम:** मेंकोजेब (Mancozeb 75% WP) - 2.5 ग्राम प्रति लीटर पानी, या कॉपर ऑक्सीक्लोराइड 3 ग्राम/लीटर।\n"
                f"2. **छिड़काव का सही समय:** सुबह 8-10 बजे या शाम 4-6 बजे जब धूप तेज न हो और हवा शांत हो।\n"
                f"3. **सावधानी:** छिड़काव के 48 घंटे तक खेत में मवेशियों को न जाने दें और स्प्रे करते समय मास्क पहनें।"
            )
        elif "water" in q or "irrigation" in q or "पानी" in q or "सिंचाई" in q:
            advice = (
                f"💧 **सिंचाई और नमी नियंत्रण:**\n\n"
                f"• {req.disease} ज्यादा नमी में तेजी से बढ़ता है। फव्वारा सिंचाई से बचें ताकि पत्तियों पर पानी न ठहरे।\n"
                f"• केवल जड़ों के पास ड्रिप या नाली द्वारा पानी दें। खेत में जलजमाव न होने दें।"
            )
        else:
            advice = (
                f"🌾 **डॉक्टर सलाह ({req.crop} - {req.disease}):**\n\n"
                f"• यह समस्या {req.severity} स्तर की है।\n"
                f"• प्राथमिक उपचार के रूप में संक्रमित पत्तियों को तुरंत हटाएं और नीम तेल 1500 PPM का छिड़काव करें।\n"
                f"• यदि रोग बढ़ रहा हो तो ट्राइकोडर्मा विरिडे (Trichoderma viride) 5 ग्राम प्रति लीटर पानी का छिड़काव करें।"
            )
    else:
        if "organic" in q or "neem" in q or "natural" in q or "home" in q:
            advice = (
                f"🌿 **Organic & Natural Treatment for {req.crop}:**\n\n"
                f"1. **Cold-Pressed Neem Oil Spray:** Mix 5 ml Neem Oil (1500 PPM) with 1 ml mild liquid soap per 1 liter of clean water. Spray both upper and lower leaf surfaces.\n"
                f"2. **Fermented Buttermilk (Khatti Chhachh):** Dilute aged buttermilk 1:4 with water. The lactic acid bacteria create a protective barrier against fungal spores.\n"
                f"3. **Sanitation:** Immediately prune and bag heavily affected leaves to halt spore transmission to neighboring plants."
            )
        elif "spray" in q or "dosage" in q or "chemical" in q or "fungicide" in q:
            advice = (
                f"🧪 **Spraying & Chemical Guide for {req.disease} in {req.crop}:**\n\n"
                f"1. **Recommended Formulation:** Mancozeb 75% WP @ 2.0-2.5 g/liter of water, or Copper Oxychloride 50% WP @ 3.0 g/liter.\n"
                f"2. **Optimal Spray Window:** Apply early morning (before 10 AM) or late afternoon (after 4 PM) under calm wind conditions (<10 km/h).\n"
                f"3. **Safety Buffer:** Maintain a 7 to 10-day pre-harvest interval (PHI) before picking produce."
            )
        elif "water" in q or "rain" in q or "humidity" in q:
            advice = (
                f"💧 **Water & Canopy Management:**\n\n"
                f"• Spores of {req.disease} thrive in persistent leaf wetness. Avoid overhead sprinkler watering.\n"
                f"• Switch to drip irrigation at root level and ensure adequate row spacing for air circulation."
            )
        else:
            advice = (
                f"🌱 **Agronomic Prescription for {req.crop} ({req.disease}):**\n\n"
                f"• Current Risk Level: **{req.severity}**.\n"
                f"• Start with biological protection (Trichoderma viride @ 5g/liter soil drench).\n"
                f"• Inspect field daily and avoid working in wet crops to prevent mechanical transmission of spores."
            )

    return {"status": "success", "answer": advice, "engine": "AgriShield Expert Advisor"}

# ============================================================
# Diseases & Crops Catalog
# ============================================================

@app.get("/api/diseases")
async def get_diseases(
    crop: Optional[str] = Query(None, description="Filter by crop name (e.g. Tomato, Apple)"),
    status: Optional[str] = Query(None, description="Filter by status (Healthy or Diseased)"),
    pathogen: Optional[str] = Query(None, description="Filter by pathogen type")
):
    if mongo_manager.is_connected:
        items = await mongo_manager.get_diseases(crop=crop, status=status, pathogen=pathogen)
        if items:
            return {"total": len(items), "source": "mongodb", "diseases": items}
            
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
