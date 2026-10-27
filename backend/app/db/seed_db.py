import os
import sys
import json
import uuid
import hashlib
import pymongo
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.dirname(APP_DIR)
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)

DATA_PATH = os.path.join(APP_DIR, "data", "disease_info.json")
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/agrishield_db")
DB_NAME = "agrishield_db"

def hash_pwd(pwd: str, salt: str):
    return hashlib.pbkdf2_hmac("sha256", pwd.encode("utf-8"), salt.encode("utf-8"), 100000).hex()

def seed_database():
    print("=" * 60)
    print("  AgriShield-AI - Database Initializer & Seeder")
    print("=" * 60)
    print(f"Connecting to MongoDB: {MONGO_URI}...")
    
    try:
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=4000)
        client.admin.command('ping')
        print("Connected to MongoDB successfully!")
    except Exception as e:
        print(f"Warning: Could not connect to MongoDB ({e}). The application will run in in-memory resilience mode.")
        return

    clean_uri = MONGO_URI.split("?")[0]
    if "/" in clean_uri.replace("mongodb://", "").replace("mongodb+srv://", ""):
        parsed_db = clean_uri.split("/")[-1]
        db_name = parsed_db if parsed_db else DB_NAME
    else:
        db_name = DB_NAME

    db = client[db_name]
    print(f"Target Database: {db_name}")

    # 1. Sync Diseases Collection
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            diseases = json.load(f)

        print(f"\nSyncing 'diseases' collection with {len(diseases)} conditions...")
        diseases_col = db["diseases"]
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
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            diseases_col.update_one(
                {"$or": [{"class_name": class_name}, {"name": common_name, "crop": crop}]},
                {"$set": doc},
                upsert=True
            )
            seeded_count += 1
        print(f"Synced {seeded_count} diseases into 'diseases' collection.")

    # 2. Seed Starter Users
    users_col = db["users"]
    users_col.create_index([("email", pymongo.ASCENDING)], unique=True, sparse=True)
    if users_col.count_documents({}) == 0:
        salt = uuid.uuid4().hex
        pwd_hash = hash_pwd("kisan123", salt)
        starter_users = [
            {
                "_id": "usr_001",
                "id": "usr_001",
                "name": "Ramesh Kumar",
                "email": "ramesh@kisan.com",
                "phone": "+919876543210",
                "password_hash": pwd_hash,
                "salt": salt,
                "role": "Farmer",
                "location": {"type": "Point", "coordinates": [75.78, 31.38]},
                "locationName": "Amritsar, Punjab",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "_id": "usr_002",
                "id": "usr_002",
                "name": "Gurpreet Singh",
                "email": "gurpreet@kisan.com",
                "phone": "+919876543211",
                "password_hash": pwd_hash,
                "salt": salt,
                "role": "Farmer",
                "location": {"type": "Point", "coordinates": [75.82, 31.40]},
                "locationName": "Karnal, Haryana",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        users_col.insert_many(starter_users)
        print("Initialized default farmer accounts in 'users' collection (Password: kisan123).")

    # 3. Seed Starter Farms
    farms_col = db["farms"]
    farms_col.create_index([("farmerId", pymongo.ASCENDING)])
    if farms_col.count_documents({}) == 0:
        default_farms = [
            {
                "_id": "farm_001",
                "id": "farm_001",
                "farmName": "Green Valley - Field 1",
                "farmerName": "Ramesh Kumar",
                "farmerId": "usr_001",
                "crop": "Tomato",
                "area": 3.5,
                "location": {"type": "Point", "coordinates": [75.78, 31.38]},
                "locationName": "Amritsar, Punjab",
                "sowingDate": "2026-06-10",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "_id": "farm_002",
                "id": "farm_002",
                "farmName": "Golden Harvest Farm",
                "farmerName": "Gurpreet Singh",
                "farmerId": "usr_002",
                "crop": "Potato",
                "area": 5.0,
                "location": {"type": "Point", "coordinates": [75.82, 31.40]},
                "locationName": "Karnal, Haryana",
                "sowingDate": "2026-06-01",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        farms_col.insert_many(default_farms)
        print("Initialized starter farm plots in 'farms' collection.")

    # 4. Crop Observations Indexing
    obs_col = db["crop_observations"]
    obs_col.create_index([("createdAt", pymongo.DESCENDING)])
    obs_col.create_index([("crop", pymongo.ASCENDING)])
    obs_col.create_index([("farmerId", pymongo.ASCENDING)])

    print("\n" + "=" * 60)
    print("  Database Seeding Successful!")
    print("=" * 60)
    print(f"  Database Name: {db_name}")
    print(f"  Collections:")
    print(f"    - diseases:           {diseases_col.count_documents({})} documents")
    print(f"    - users:              {users_col.count_documents({})} documents")
    print(f"    - farms:              {farms_col.count_documents({})} documents")
    print(f"    - crop_observations:  {obs_col.count_documents({})} documents")
    print("=" * 60)

if __name__ == "__main__":
    seed_database()
