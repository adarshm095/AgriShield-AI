import os
import json
import logging
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import pymongo

logger = logging.getLogger("agrishield.mongo")

DEFAULT_MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/agrishield_db")
DB_NAME = "agrishield_db"

class MongoDBManager:
    def __init__(self):
        self.uri = DEFAULT_MONGO_URI
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.is_connected = False
        self.connection_error: Optional[str] = None

    async def ensure_connected(self):
        import asyncio
        if self.client is not None:
            try:
                if self.client.get_io_loop().is_closed():
                    self.client = None
                    self.db = None
                    self.is_connected = False
            except Exception:
                pass
        if not self.is_connected or self.client is None:
            await self.connect()

    async def connect(self):
        try:
            self.uri = os.getenv("MONGODB_URI", DEFAULT_MONGO_URI)
            logger.info(f"Connecting to MongoDB at: {self._masked_uri()}")
            self.client = AsyncIOMotorClient(
                self.uri,
                serverSelectionTimeoutMS=3000,
                connectTimeoutMS=3000
            )
            # Ping database to verify connection
            await self.client.admin.command('ping')
            
            # Extract database name if present in URI
            clean_uri = self.uri.split("?")[0]
            if "/" in clean_uri.replace("mongodb://", "").replace("mongodb+srv://", ""):
                parsed_db = clean_uri.split("/")[-1]
                target_db = parsed_db if parsed_db else DB_NAME
            else:
                target_db = DB_NAME
                
            self.db = self.client[target_db]
            self.is_connected = True
            self.connection_error = None
            logger.info(f"Connected to MongoDB database '{self.db.name}' successfully.")
            
            # Ensure indexes & enrich database
            await self._ensure_indexes()
            await self._auto_enrich_diseases()
            
        except Exception as e:
            self.is_connected = False
            self.connection_error = str(e)
            logger.warning(f"MongoDB connection failed: {e}. Fallback to in-memory mode.")

    def _masked_uri(self) -> str:
        if "@" in self.uri:
            prefix = self.uri.split("@")[0]
            host = self.uri.split("@")[1]
            schema = prefix.split("://")[0]
            return f"{schema}://****:****@{host}"
        return self.uri

    async def _ensure_indexes(self):
        if not self.is_connected or self.db is None:
            return
        try:
            # We index on 'name' and 'crop' for diseases without forcing unique on class_name if old docs exist
            await self.db.diseases.create_index([("name", pymongo.ASCENDING)])
            await self.db.diseases.create_index([("crop", pymongo.ASCENDING)])
            await self.db.crop_observations.create_index([("createdAt", pymongo.DESCENDING)])
            await self.db.crop_observations.create_index([("crop", pymongo.ASCENDING)])
            await self.db.crop_observations.create_index([("farmId", pymongo.ASCENDING)])
            await self.db.farms.create_index([("farmerId", pymongo.ASCENDING)])
        except Exception as e:
            logger.warning(f"Could not create MongoDB indexes: {e}")

    async def _auto_enrich_diseases(self):
        """Enrich existing diseases collection with all 38 classes if not all are present"""
        if not self.is_connected or self.db is None:
            return
        try:
            count = await self.db.diseases.count_documents({})
            if count < 38:
                logger.info(f"MongoDB 'diseases' has {count} documents. Syncing all 38 conditions...")
                await self.seed_diseases()
        except Exception as e:
            logger.warning(f"Auto-enrich check failed: {e}")

    async def seed_diseases(self, force=False):
        if not self.is_connected or self.db is None:
            return 0
            
        script_dir = os.path.dirname(os.path.abspath(__file__))
        app_dir = os.path.dirname(script_dir)
        db_path = os.path.join(app_dir, "data", "disease_info.json")
        
        if not os.path.exists(db_path):
            return 0
            
        with open(db_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        if force:
            await self.db.diseases.delete_many({})
            
        count = 0
        for class_name, details in data.items():
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
                    f"Favorable conditions for {details.get('pathogen_type', 'disease')} pathogen proliferation",
                    "Elevated relative humidity and prolonged canopy leaf moisture"
                ],
                "updated_at": datetime.utcnow()
            }
            # Upsert by either class_name or name+crop
            await self.db.diseases.update_one(
                {"$or": [{"class_name": class_name}, {"name": common_name, "crop": crop}]},
                {"$set": doc},
                upsert=True
            )
            count += 1
            
        logger.info(f"Seeded/updated {count} diseases in MongoDB.")
        return count

    async def get_status(self) -> Dict[str, Any]:
        await self.ensure_connected()
        if not self.is_connected or self.db is None:
            return {
                "connected": False,
                "uri": self._masked_uri(),
                "error": self.connection_error,
                "database": DB_NAME,
                "compass_connection_string": "mongodb://localhost:27017/agrishield_db",
                "collections": {
                    "diseases": 0,
                    "crop_observations": 0,
                    "farms": 0,
                    "users": 0
                }
            }
            
        try:
            diseases_count = await self.db.diseases.count_documents({})
            obs_count = await self.db.crop_observations.count_documents({})
            farms_count = await self.db.farms.count_documents({})
            users_count = await self.db.users.count_documents({})
            
            return {
                "connected": True,
                "uri": self._masked_uri(),
                "database": self.db.name,
                "compass_connection_string": self.uri if "mongodb+srv" not in self.uri else self._masked_uri(),
                "collections": {
                    "diseases": diseases_count,
                    "crop_observations": obs_count,
                    "farms": farms_count,
                    "users": users_count
                }
            }
        except Exception as e:
            return {
                "connected": False,
                "uri": self._masked_uri(),
                "error": str(e),
                "database": DB_NAME
            }

    async def get_farms(self) -> List[Dict[str, Any]]:
        await self.ensure_connected()
        if not self.is_connected or self.db is None:
            return []
        try:
            cursor = self.db.farms.find({})
            farms = []
            async for doc in cursor:
                if "_id" in doc:
                    doc["id"] = str(doc.pop("_id"))
                farms.append(doc)
            return farms
        except Exception as e:
            logger.error(f"Error fetching farms: {e}")
            return []

    async def get_diseases(self, crop: Optional[str] = None, status: Optional[str] = None, pathogen: Optional[str] = None) -> List[Dict[str, Any]]:
        await self.ensure_connected()
        if not self.is_connected or self.db is None:
            return []
        try:
            query = {}
            if crop:
                query["crop"] = {"$regex": f"^{crop}$", "$options": "i"}
            if status:
                query["status"] = {"$regex": f"^{status}$", "$options": "i"}
            if pathogen:
                query["pathogen_type"] = {"$regex": pathogen, "$options": "i"}
                
            cursor = self.db.diseases.find(query)
            items = []
            async for doc in cursor:
                doc["id"] = str(doc.pop("_id"))
                if "updated_at" in doc and isinstance(doc["updated_at"], datetime):
                    doc["updated_at"] = doc["updated_at"].isoformat()
                items.append(doc)
            return items
        except Exception as e:
            logger.error(f"Error fetching diseases from MongoDB: {e}")
            return []

    async def save_observation(self, prediction_data: Dict[str, Any], farm_id: Optional[str] = None, farmer_name: Optional[str] = None, image_url: Optional[str] = None) -> Dict[str, Any]:
        await self.ensure_connected()
        if not self.is_connected or self.db is None:
            return {}
            
        primary = prediction_data.get("primary", {})
        crop = primary.get("crop", "Unknown")
        disease_name = primary.get("common_name", primary.get("class_name", "Unknown"))
        severity = primary.get("severity", "Moderate")
        confidence_pct = primary.get("confidence", 95.0)
        confidence_ratio = round(confidence_pct / 100.0, 3)
        
        # Risk score computation
        is_healthy = (primary.get("status") or "").lower() == "healthy"
        if is_healthy:
            risk_level = "LOW"
            risk_score = 12.0
            risk_summary = f"Crop {crop} exhibits optimal health. Zero pathogen threats identified."
        elif "severe" in severity.lower():
            risk_level = "CRITICAL"
            risk_score = 88.5
            risk_summary = f"CRITICAL risk of {disease_name} spread across {crop} foliage."
        elif "high" in severity.lower():
            risk_level = "HIGH"
            risk_score = 76.0
            risk_summary = f"HIGH risk of {disease_name} spread based on neural confidence."
        else:
            risk_level = "MODERATE"
            risk_score = 48.0
            risk_summary = f"MODERATE risk of {disease_name} infection."
            
        doc_id = f"obs_{uuid.uuid4().hex[:10]}"
        obs_doc = {
            "_id": doc_id,
            "farmId": farm_id or "farm_001",
            "farmerName": farmer_name or "Ramesh Kumar",
            "crop": crop,
            "imageUrl": image_url or f"/static/samples/{prediction_data.get('filename', 'leaf.jpg')}",
            "environment": {
                "temperature": 25.5,
                "humidity": 86.0,
                "soilMoisture": 78.0,
                "rainfall": 4.5,
                "soilPh": 6.7
            },
            "prediction": {
                "disease": disease_name,
                "confidence": confidence_ratio,
                "confidence_percent": confidence_pct,
                "organ": "Leaf",
                "class_name": primary.get("class_name")
            },
            "riskLevel": risk_level,
            "riskScore": risk_score,
            "riskSummary": risk_summary,
            "contributingFactors": primary.get("symptoms", [
                "Elevated relative humidity facilitating pathogen spore mobility.",
                "Surface moisture on leaf canopy."
            ]),
            "location": {
                "type": "Point",
                "coordinates": [75.78, 31.38]
            },
            "createdAt": datetime.utcnow().isoformat(),
            "curativeActions": primary.get("chemical_treatment", []) + primary.get("organic_treatment", []),
            "prevention": primary.get("prevention", []),
            "alternates": prediction_data.get("alternates", [])
        }
        
        try:
            await self.db.crop_observations.insert_one(obs_doc)
            logger.info(f"Saved observation '{doc_id}' into MongoDB 'crop_observations'.")
            return obs_doc
        except Exception as e:
            logger.error(f"Error saving crop observation to MongoDB: {e}")
            return {}

    async def get_observations(self, limit=50) -> List[Dict[str, Any]]:
        await self.ensure_connected()
        if not self.is_connected or self.db is None:
            return []
        try:
            cursor = self.db.crop_observations.find({}).sort("createdAt", pymongo.DESCENDING).limit(limit)
            observations = []
            async for doc in cursor:
                doc["id"] = str(doc["_id"])
                observations.append(doc)
            return observations
        except Exception as e:
            logger.error(f"Error fetching crop observations: {e}")
            return []

    async def delete_observation(self, obs_id: str) -> bool:
        if not self.is_connected or self.db is None:
            return False
        try:
            res = await self.db.crop_observations.delete_one({"_id": obs_id})
            return res.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete observation: {e}")
            return False

# Singleton instance
mongo_manager = MongoDBManager()
