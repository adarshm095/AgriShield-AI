import os
import sys
import unittest
from fastapi.testclient import TestClient

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
sys.path.insert(0, BACKEND_DIR)

from app.main import app

class TestAgriShieldAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_client_ctx = TestClient(app)
        cls.client = cls.test_client_ctx.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.test_client_ctx.__exit__(None, None, None)

    def test_health(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "online")
        self.assertTrue(data["model_loaded"])
        self.assertEqual(data["total_classes"], 38)
        self.assertIn("mongodb", data)

    def test_mongodb_status(self):
        res = self.client.get("/api/db/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("connected", data)
        self.assertIn("database", data)
        self.assertIn("collections", data)

    def test_farms(self):
        res = self.client.get("/api/farms")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("farms", data)
        self.assertGreaterEqual(data["total"], 1)

    def test_diseases_catalog(self):
        res = self.client.get("/api/diseases")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(data["total"], 38)

    def test_crops(self):
        res = self.client.get("/api/crops")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(data["total_crops"], 10)

    def test_predict_sample_and_mongo_logging(self):
        res = self.client.post("/api/predict-sample/tomato_early_blight?farm_id=farm_001")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("primary", data)
        self.assertEqual(data["primary"]["crop"], "Tomato")
        self.assertGreater(data["primary"]["confidence"], 50.0)
        self.assertIn("organic_treatment", data["primary"])
        self.assertIn("chemical_treatment", data["primary"])
        self.assertIn("prevention", data["primary"])
        # Verify MongoDB auto-persisted
        self.assertIn("mongo_saved", data)

    def test_observations(self):
        res = self.client.get("/api/observations")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("observations", data)
        self.assertGreater(data["total"], 0)

    def test_index_page(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("AgriShield-AI", res.text)

    def test_auth_registration_and_login(self):
        test_email = "farmer_test@example.com"
        reg_payload = {
            "name": "Devendra Patil",
            "email": test_email,
            "password": "farmerSecret123",
            "phone": "+919876543210",
            "location": "Nashik, Maharashtra"
        }
        res = self.client.post("/api/auth/register", json=reg_payload)
        self.assertIn(res.status_code, [200, 400]) # 200 or 400 if already registered from prev run
        
        # Test Login
        login_res = self.client.post("/api/auth/login", json={"identifier": test_email, "password": "farmerSecret123"})
        self.assertEqual(login_res.status_code, 200)
        data = login_res.json()
        self.assertIn("token", data)
        self.assertEqual(data["user"]["name"], "Devendra Patil")

        # Test Auth Me
        token = data["token"]
        me_res = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(me_res.status_code, 200)
        self.assertEqual(me_res.json()["user"]["email"], test_email)

    def test_create_dynamic_farm(self):
        farm_payload = {
            "farmName": "Patil Vineyard - Block 4",
            "crop": "Grape",
            "area": 4.2,
            "location": "Nashik, Maharashtra",
            "farmerName": "Devendra Patil"
        }
        res = self.client.post("/api/farms", json=farm_payload)
        self.assertEqual(res.status_code, 200)
        farm_data = res.json()["farm"]
        self.assertEqual(farm_data["farmName"], "Patil Vineyard - Block 4")
        self.assertEqual(farm_data["crop"], "Grape")

    def test_ai_advisor(self):
        advisor_payload = {
            "question": "How to make organic spray using neem oil?",
            "crop": "Tomato",
            "disease": "Early Blight",
            "severity": "Moderate",
            "language": "en"
        }
        res = self.client.post("/api/ai/advisor", json=advisor_payload)
        self.assertEqual(res.status_code, 200)
        self.assertIn("answer", res.json())
        self.assertIn("Neem", res.json()["answer"])

if __name__ == "__main__":
    unittest.main()

