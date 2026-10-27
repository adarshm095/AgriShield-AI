import os
import json
import logging
import uuid
import hashlib
import hmac
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import pymongo

logger = logging.getLogger("agrishield.mongo")

DEFAULT_MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/agrishield_db")
DB_NAME = "agrishield_db"

def current_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class MongoDBManager:
    def __init__(self):
        self.uri = DEFAULT_MONGO_URI
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.is_connected = False
        self.connection_error: Optional[str] = None

        # Robust In-Memory Fallback stores for offline / development resilience
        self.fallback_users: Dict[str, Dict[str, Any]] = {}
        self.fallback_sessions: Dict[str, str] = {}  # token -> user_id
        self.fallback_farms: List[Dict[str, Any]] = [
            {
                "_id": "farm_001",
                "id": "farm_001",
                "farmName": "Green Valley - Field 1",
                "farmerName": "Ramesh Kumar",
                "farmerId": "usr_001",
                "crop": "Tomato",
                "area": 3.5,
                "location": "Amritsar, Punjab",
                "sowingDate": "2026-06-10"
            },
            {
                "_id": "farm_002",
                "id": "farm_002",
                "farmName": "Golden Harvest Farm",
                "farmerName": "Gurpreet Singh",
                "farmerId": "usr_002",
                "crop": "Potato",
                "area": 5.0,
                "location": "Karnal, Haryana",
                "sowingDate": "2026-06-01"
            },
            {
                "_id": "farm_003",
                "id": "farm_003",
                "farmName": "Sunshine Organic Fields",
                "farmerName": "Sunita Devi",
                "farmerId": "usr_003",
                "crop": "Corn",
                "area": 2.8,
                "location": "Varanasi, UP",
                "sowingDate": "2026-05-20"
            }
        ]
        self.fallback_observations: List[Dict[str, Any]] = []

    async def ensure_connected(self):
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
            await self._auto_seed_default_farms()
            
        except Exception as e:
            self.is_connected = False
            self.connection_error = str(e)
            logger.warning(f"MongoDB connection failed: {e}. Fallback to resilient in-memory mode.")

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
            await self.db.diseases.create_index([("name", pymongo.ASCENDING)])
            await self.db.diseases.create_index([("crop", pymongo.ASCENDING)])
            await self.db.crop_observations.create_index([("createdAt", pymongo.DESCENDING)])
            await self.db.crop_observations.create_index([("crop", pymongo.ASCENDING)])
            await self.db.crop_observations.create_index([("farmId", pymongo.ASCENDING)])
            await self.db.crop_observations.create_index([("farmerId", pymongo.ASCENDING)])
            await self.db.farms.create_index([("farmerId", pymongo.ASCENDING)])
            await self.db.users.create_index([("email", pymongo.ASCENDING)], unique=True, sparse=True)
            await self.db.users.create_index([("phone", pymongo.ASCENDING)], sparse=True)
            await self.db.sessions.create_index([("token", pymongo.ASCENDING)], unique=True)
        except Exception as e:
            logger.warning(f"Could not create MongoDB indexes: {e}")

    async def _auto_seed_default_farms(self):
        if not self.is_connected or self.db is None:
            return
        try:
            count = await self.db.farms.count_documents({})
            if count == 0:
                for f in self.fallback_farms:
                    doc = dict(f)
                    doc["_id"] = doc.get("id", doc.get("_id"))
                    await self.db.farms.insert_one(doc)
                logger.info("Initialized default starter farms in MongoDB.")
        except Exception as e:
            logger.warning(f"Default farms seed check error: {e}")

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
                "updated_at": current_utc_iso()
            }
            await self.db.diseases.update_one(
                {"$or": [{"class_name": class_name}, {"name": common_name, "crop": crop}]},
                {"$set": doc},
                upsert=True
            )
            count += 1
            
        logger.info(f"Seeded/updated {count} diseases in MongoDB.")
        return count

    # ============================================================
    # Authentication & User Management
    # ============================================================
    def hash_password(self, password: str, salt: Optional[str] = None) -> tuple[str, str]:
        if not salt:
            salt = uuid.uuid4().hex
        pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
        return pwd_hash, salt

    def verify_password(self, password: str, stored_hash: str, salt: str) -> bool:
        pwd_hash, _ = self.hash_password(password, salt)
        return hmac.compare_digest(pwd_hash, stored_hash)

    def _sanitize_user(self, user_doc: Dict[str, Any]) -> Dict[str, Any]:
        safe = dict(user_doc)
        if "_id" in safe:
            safe["id"] = str(safe.pop("_id"))
        safe.pop("password_hash", None)
        safe.pop("salt", None)
        return safe

    async def register_user(self, name: str, email: str, password: str, phone: Optional[str] = None, role: str = "Farmer", location: str = "") -> Dict[str, Any]:
        await self.ensure_connected()
        norm_email = email.strip().lower()
        
        # Check existing user
        if self.is_connected and self.db is not None:
            existing = await self.db.users.find_one({"$or": [{"email": norm_email}, {"phone": phone} if phone else {"email": norm_email}]})
            if existing:
                raise ValueError("An account with this email or phone number already exists.")
        else:
            for u in self.fallback_users.values():
                if u.get("email") == norm_email or (phone and u.get("phone") == phone):
                    raise ValueError("An account with this email or phone number already exists.")

        user_id = f"usr_{uuid.uuid4().hex[:10]}"
        pwd_hash, salt = self.hash_password(password)
        created_at = current_utc_iso()

        loc_text = location.strip() if isinstance(location, str) else "Local Farm"
        loc_geo = location if (isinstance(location, dict) and "coordinates" in location) else {"type": "Point", "coordinates": [75.78, 31.38]}

        user_doc = {
            "_id": user_id,
            "id": user_id,
            "name": name.strip(),
            "email": norm_email,
            "phone": phone.strip() if phone else "",
            "password_hash": pwd_hash,
            "salt": salt,
            "role": role,
            "location": loc_geo,
            "locationName": loc_text,
            "address": loc_text,
            "created_at": created_at
        }

        # Create session token
        session_token = f"agt_{uuid.uuid4().hex}"
        session_doc = {
            "token": session_token,
            "user_id": user_id,
            "created_at": created_at
        }

        if self.is_connected and self.db is not None:
            await self.db.users.insert_one(user_doc)
            await self.db.sessions.insert_one(session_doc)
        else:
            self.fallback_users[user_id] = user_doc
            self.fallback_sessions[session_token] = user_id

        # Also auto-create a starter default farm for the new farmer
        await self.create_farm({
            "farmName": f"{name.strip()}'s Main Field",
            "farmerName": name.strip(),
            "farmerId": user_id,
            "crop": "Tomato",
            "area": 2.5,
            "location": location.strip() or "Local Farm",
            "sowingDate": datetime.now().strftime("%Y-%m-%d")
        })

        return {
            "token": session_token,
            "user": self._sanitize_user(user_doc)
        }

    async def login_user(self, identifier: str, password: str) -> Dict[str, Any]:
        await self.ensure_connected()
        norm_id = identifier.strip().lower()

        user_doc = None
        if self.is_connected and self.db is not None:
            user_doc = await self.db.users.find_one({"$or": [{"email": norm_id}, {"phone": identifier.strip()}]})
        else:
            for u in self.fallback_users.values():
                if u.get("email") == norm_id or u.get("phone") == identifier.strip():
                    user_doc = u
                    break

        if not user_doc:
            raise ValueError("Invalid email or password. Please check your credentials.")

        if not self.verify_password(password, user_doc.get("password_hash", ""), user_doc.get("salt", "")):
            raise ValueError("Invalid email or password. Please check your credentials.")

        session_token = f"agt_{uuid.uuid4().hex}"
        user_id = str(user_doc.get("id") or user_doc.get("_id"))
        session_doc = {
            "token": session_token,
            "user_id": user_id,
            "created_at": current_utc_iso()
        }

        if self.is_connected and self.db is not None:
            await self.db.sessions.insert_one(session_doc)
        else:
            self.fallback_sessions[session_token] = user_id

        return {
            "token": session_token,
            "user": self._sanitize_user(user_doc)
        }

    async def get_user_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        if not token:
            return None
        await self.ensure_connected()

        user_id = None
        if self.is_connected and self.db is not None:
            sess = await self.db.sessions.find_one({"token": token})
            if sess:
                user_id = sess.get("user_id")
                user = await self.db.users.find_one({"_id": user_id})
                if user:
                    return self._sanitize_user(user)
        else:
            user_id = self.fallback_sessions.get(token)
            if user_id and user_id in self.fallback_users:
                return self._sanitize_user(self.fallback_users[user_id])
        return None

    # ============================================================
    # Dynamic Farms Management
    # ============================================================
    async def create_farm(self, farm_data: Dict[str, Any]) -> Dict[str, Any]:
        await self.ensure_connected()
        farm_id = f"farm_{uuid.uuid4().hex[:8]}"
        raw_loc = farm_data.get("location")
        if isinstance(raw_loc, dict) and "coordinates" in raw_loc:
            loc_geo = raw_loc
            loc_text = str(raw_loc.get("name", "Local Field"))
        else:
            loc_text = str(raw_loc or "Local Field")
            loc_geo = {"type": "Point", "coordinates": [75.78, 31.38]}

        doc = {
            "_id": farm_id,
            "id": farm_id,
            "farmName": farm_data.get("farmName", "My Crop Field"),
            "farmerName": farm_data.get("farmerName", "Farmer"),
            "farmerId": farm_data.get("farmerId", "usr_guest"),
            "crop": farm_data.get("crop", "Tomato"),
            "area": float(farm_data.get("area", 1.0)),
            "location": loc_geo,
            "locationName": loc_text,
            "address": loc_text,
            "sowingDate": farm_data.get("sowingDate") or datetime.now().strftime("%Y-%m-%d"),
            "created_at": current_utc_iso()
        }

        if self.is_connected and self.db is not None:
            await self.db.farms.insert_one(doc)
        else:
            self.fallback_farms.insert(0, doc)

        clean = dict(doc)
        if "_id" in clean:
            clean["id"] = str(clean.pop("_id"))
        return clean

    async def get_farms(self, farmer_id: Optional[str] = None) -> List[Dict[str, Any]]:
        await self.ensure_connected()
        if self.is_connected and self.db is not None:
            try:
                query = {}
                if farmer_id:
                    query = {"farmerId": farmer_id}
                cursor = self.db.farms.find(query)
                farms = []
                async for doc in cursor:
                    doc["id"] = str(doc.pop("_id", doc.get("id")))
                    farms.append(doc)
                # If specific farmer has no farms yet, return defaults so dropdown is never broken
                if not farms and farmer_id:
                    cursor_all = self.db.farms.find({}).limit(5)
                    async for doc in cursor_all:
                        doc["id"] = str(doc.pop("_id", doc.get("id")))
                        farms.append(doc)
                return farms
            except Exception as e:
                logger.error(f"Error fetching farms: {e}")
                return self.fallback_farms
        else:
            if farmer_id:
                matched = [f for f in self.fallback_farms if f.get("farmerId") == farmer_id]
                return matched if matched else self.fallback_farms
            return self.fallback_farms

    # ============================================================
    # Diseases Catalog
    # ============================================================
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

    # ============================================================
    # Crop Observations / Scan Records
    # ============================================================
    async def save_observation(self, prediction_data: Dict[str, Any], farm_id: Optional[str] = None, farmer_name: Optional[str] = None, farmer_id: Optional[str] = None, image_url: Optional[str] = None) -> Dict[str, Any]:
        await self.ensure_connected()
            
        primary = prediction_data.get("primary", {})
        crop = primary.get("crop", "Unknown")
        disease_name = primary.get("common_name", primary.get("class_name", "Unknown"))
        severity = primary.get("severity", "Moderate")
        confidence_pct = primary.get("confidence", 95.0)
        confidence_ratio = round(confidence_pct / 100.0, 3)
        
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
            risk_summary = f"HIGH risk of {disease_name} spread based on confidence."
        else:
            risk_level = "MODERATE"
            risk_score = 48.0
            risk_summary = f"MODERATE risk of {disease_name} infection."
            
        doc_id = f"scan_{uuid.uuid4().hex[:10]}"
        obs_doc = {
            "_id": doc_id,
            "id": doc_id,
            "farmId": farm_id or "farm_001",
            "farmerName": farmer_name or "Farmer",
            "farmerId": farmer_id or "usr_guest",
            "crop": crop,
            "imageUrl": image_url or f"/static/samples/{prediction_data.get('filename', 'leaf.jpg')}",
            "environment": {
                "temperature": 25.5,
                "humidity": 84.0,
                "soilMoisture": 72.0,
                "rainfall": 2.5
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
                "Relative humidity facilitating fungal spore proliferation.",
                "Surface foliage moisture."
            ]),
            "createdAt": current_utc_iso(),
            "curativeActions": primary.get("chemical_treatment", []) + primary.get("organic_treatment", []),
            "organic_treatment": primary.get("organic_treatment", []),
            "chemical_treatment": primary.get("chemical_treatment", []),
            "prevention": primary.get("prevention", []),
            "alternates": prediction_data.get("alternates", [])
        }
        
        if self.is_connected and self.db is not None:
            try:
                await self.db.crop_observations.insert_one(obs_doc)
                logger.info(f"Saved observation '{doc_id}' into MongoDB 'crop_observations'.")
            except Exception as e:
                logger.error(f"Error saving crop observation to MongoDB: {e}")
        else:
            self.fallback_observations.insert(0, obs_doc)

        clean = dict(obs_doc)
        if "_id" in clean:
            clean["id"] = str(clean.pop("_id"))
        return clean

    async def get_observations(self, farmer_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        await self.ensure_connected()
        if self.is_connected and self.db is None:
            return self.fallback_observations[:limit]

        if self.is_connected and self.db is not None:
            try:
                query = {}
                if farmer_id:
                    query["farmerId"] = farmer_id
                cursor = self.db.crop_observations.find(query).sort("createdAt", pymongo.DESCENDING).limit(limit)
                observations = []
                async for doc in cursor:
                    doc["id"] = str(doc.pop("_id", doc.get("id")))
                    observations.append(doc)
                return observations
            except Exception as e:
                logger.error(f"Error fetching crop observations: {e}")
                return self.fallback_observations[:limit]
        else:
            if farmer_id:
                return [o for o in self.fallback_observations if o.get("farmerId") == farmer_id][:limit]
            return self.fallback_observations[:limit]

    async def delete_observation(self, obs_id: str) -> bool:
        if self.is_connected and self.db is not None:
            try:
                res = await self.db.crop_observations.delete_one({"_id": obs_id})
                return res.deleted_count > 0
            except Exception as e:
                logger.error(f"Failed to delete observation: {e}")
                return False
        else:
            init_len = len(self.fallback_observations)
            self.fallback_observations = [o for o in self.fallback_observations if o.get("_id") != obs_id and o.get("id") != obs_id]
            return len(self.fallback_observations) < init_len

    async def get_status(self) -> Dict[str, Any]:
        await self.ensure_connected()
        if not self.is_connected or self.db is None:
            return {
                "connected": False,
                "status": "In-Memory Mode",
                "database": DB_NAME,
                "collections": {
                    "diseases": 38,
                    "crop_observations": len(self.fallback_observations),
                    "farms": len(self.fallback_farms),
                    "users": len(self.fallback_users)
                }
            }
            
        try:
            diseases_count = await self.db.diseases.count_documents({})
            obs_count = await self.db.crop_observations.count_documents({})
            farms_count = await self.db.farms.count_documents({})
            users_count = await self.db.users.count_documents({})
            
            return {
                "connected": True,
                "status": "MongoDB Connected",
                "database": self.db.name,
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
                "error": str(e),
                "database": DB_NAME
            }

# Singleton instance
mongo_manager = MongoDBManager()
