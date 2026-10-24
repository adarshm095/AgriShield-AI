import os
import sys
import json
import pymongo
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.dirname(APP_DIR)
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)

DATA_PATH = os.path.join(APP_DIR, "data", "disease_info.json")
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/agrishield_db")
DB_NAME = "agrishield_db"

def seed_database():
    print("=" * 60)
    print("  AgriShield-AI - MongoDB Seeder")
    print("=" * 60)
    print(f"Connecting to MongoDB: {MONGO_URI}...")
    
    try:
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=4000)
        client.admin.command('ping')
        print("Connected to MongoDB successfully!")
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        print("Please ensure MongoDB is running or your Atlas connection string is correct.")
        sys.exit(1)

    clean_uri = MONGO_URI.split("?")[0]
    if "/" in clean_uri.replace("mongodb://", "").replace("mongodb+srv://", ""):
        parsed_db = clean_uri.split("/")[-1]
        db_name = parsed_db if parsed_db else DB_NAME
    else:
        db_name = DB_NAME

    db = client[db_name]
    print(f"Target Database: {db_name}")

    if not os.path.exists(DATA_PATH):
        print(f"Error: Disease database not found at {DATA_PATH}")
        sys.exit(1)

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        diseases = json.load(f)

    # 1. Sync & Enrich Diseases Collection
    print(f"\nEnriching 'diseases' collection with {len(diseases)} conditions...")
    diseases_col = db["diseases"]
    
    # Create non-unique indexes on common search fields
    diseases_col.create_index([("name", pymongo.ASCENDING)])
    diseases_col.create_index([("crop", pymongo.ASCENDING)])
    diseases_col.create_index([("pathogen_type", pymongo.ASCENDING)])
    
    seeded_count = 0
    for class_name, details in diseases.items():
        common_name = details.get("common_name", class_name)
        crop = details.get("crop", "Unknown")
        
        doc = {
            "name": common_name,
            "crop": crop,
            "class_name": class_name,
            "scientific_name": details.get("scientific_name"),
            "common_name": common_name,
            "status": details.get("status"),
            "pathogen_type": details.get("pathogen_type"),
            "severity": details.get("severity"),
            "description": details.get("description"),
            "symptoms": details.get("symptoms", []),
            "organic_treatment": details.get("organic_treatment", []),
            "chemical_treatment": details.get("chemical_treatment", []),
            "curativeActions": details.get("chemical_treatment", []) + details.get("organic_treatment", []),
            "prevention": details.get("prevention", []),
            "riskFactors": [
                f"Favorable conditions for {details.get('pathogen_type', 'disease')} proliferation",
                "High relative humidity (>80%) and prolonged foliage moisture"
            ],
            "updated_at": datetime.utcnow()
        }
        
        diseases_col.update_one(
            {"$or": [{"class_name": class_name}, {"name": common_name, "crop": crop}]},
            {"$set": doc},
            upsert=True
        )
        seeded_count += 1

    print(f"Synced {seeded_count} diseases into 'diseases' collection.")

    # 2. Verify / Ensure Farms
    farms_col = db["farms"]
    if farms_col.count_documents({}) == 0:
        default_farms = [
            {
                "_id": "farm_001",
                "farmName": "Green Acres - Plot A",
                "farmerName": "Ramesh Kumar",
                "farmerId": "usr_001",
                "crop": "Tomato",
                "area": 3.5,
                "location": {"type": "Point", "coordinates": [75.78, 31.38]},
                "sowingDate": "2026-06-10"
            },
            {
                "_id": "farm_002",
                "farmName": "Golden Harvest Farm",
                "farmerName": "Gurpreet Singh",
                "farmerId": "usr_002",
                "crop": "Potato",
                "area": 5.0,
                "location": {"type": "Point", "coordinates": [75.82, 31.40]},
                "sowingDate": "2026-06-01"
            },
            {
                "_id": "farm_003",
                "farmName": "Sunshine Fields",
                "farmerName": "Sunita Devi",
                "farmerId": "usr_003",
                "crop": "Corn",
                "area": 2.8,
                "location": {"type": "Point", "coordinates": [75.75, 31.35]},
                "sowingDate": "2026-05-20"
            }
        ]
        farms_col.insert_many(default_farms)
        print("Initialized 3 default farm records in 'farms' collection.")

    # 3. Verify / Ensure Crop Observations
    obs_col = db["crop_observations"]
    obs_col.create_index([("createdAt", pymongo.DESCENDING)])
    obs_col.create_index([("crop", pymongo.ASCENDING)])

    print("\n" + "=" * 60)
    print("  MongoDB Seeding Successful!")
    print("=" * 60)
    print(f"  Database Name: {db_name}")
    print(f"  Collections:")
    print(f"    - diseases:           {diseases_col.count_documents({})} documents")
    print(f"    - farms:              {farms_col.count_documents({})} documents")
    print(f"    - crop_observations:  {obs_col.count_documents({})} documents")
    print(f"\n  To inspect in MongoDB Compass:")
    print(f"    1. Open MongoDB Compass GUI")
    print(f"    2. Paste URI: {MONGO_URI}")
    print(f"    3. Click Connect -> View database '{db_name}'")
    print("=" * 60)

if __name__ == "__main__":
    seed_database()
