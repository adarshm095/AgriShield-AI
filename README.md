# 🌿 AgriShield-AI: Intelligent Plant Disease Diagnosis & Agronomic Protection

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.2+-ee4c2c.svg?style=flat&logo=pytorch&logoColor=white)](https://pytorch.org)
[![MongoDB](https://img.shields.io/badge/Database-MongoDB%20Atlas%20%26%20Compass-47A248.svg?style=flat&logo=mongodb&logoColor=white)](https://www.mongodb.com)
[![Accuracy](https://img.shields.io/badge/Test%20Accuracy-93.75%25-brightgreen.svg)]()
[![Model](https://img.shields.io/badge/Architecture-MobileNetV3--Small-blue.svg)]()
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)]()

**AgriShield-AI** is a production-ready, end-to-end plant pathology diagnosis and agronomic decision-support platform powered by **PyTorch Deep Learning** and backed by **MongoDB (Atlas & Compass GUI)**. AgriShield-AI detects **38 crop diseases and healthy states across 14 agricultural crops** with sub-second inference, auto-persisting every scan record, telemetry vector, and treatment protocol directly into MongoDB.

---

## 🍃 MongoDB Architecture, Atlas & Compass GUI

AgriShield-AI uses MongoDB as its primary persistence and telemetry layer. You can host the database in the cloud on **MongoDB Atlas** or inspect and query collections locally using the **MongoDB Compass GUI**.

### 1. Database Schema (`agrishield_db`)

| Collection | Description | Key Fields / Indexes |
| :--- | :--- | :--- |
| **`diseases`** | 38 plant pathology profiles | `name`, `crop`, `class_name`, `pathogen_type`, `severity`, `symptoms`, `organic_treatment`, `chemical_treatment`, `prevention` |
| **`farms`** | Registered farms & plot owners | `_id`, `farmName`, `farmerName`, `crop`, `area`, `location` (GeoJSON Point), `sowingDate` |
| **`crop_observations`** | Live leaf scans & neural diagnoses | `_id` (`obs_...`), `farmId`, `farmerName`, `crop`, `prediction` (disease, confidence), `riskLevel`, `riskScore`, `environment` (temp, humidity, moisture, pH), `createdAt` |
| **`users`** | Farmer profiles & credentials | `_id`, `name`, `role`, `contact` |

---

### 2. Inspecting Collections in MongoDB Compass

1. Launch **MongoDB Compass**.
2. In the *New Connection* screen, paste your connection string:
   - **Local MongoDB**: `mongodb://localhost:27017/agrishield_db`
   - **MongoDB Atlas (Cloud)**: `mongodb+srv://<username>:<password>@cluster0.mongodb.net/agrishield_db`
3. Click **Connect**.
4. Open the database **`agrishield_db`**.
5. Visually explore:
   - Click **`crop_observations`** to see newly diagnosed leaf scans with confidence ratings and risk scores.
   - Click **`diseases`** to view and edit treatment guidelines.
   - Click **`farms`** to view registered farm plots.

---

### 3. Connecting to MongoDB Atlas (Cloud)

To connect AgriShield-AI to MongoDB Atlas in production:
1. Create a free cluster on [MongoDB Atlas](https://www.mongodb.com/cloud/atlas).
2. Go to **Database Access** and create a database user and password.
3. Under **Network Access**, whitelist your IP or allow access from anywhere (`0.0.0.0/0`).
4. Copy your connection string from the Atlas dashboard:
   ```env
   MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/agrishield_db?retryWrites=true&w=majority
   ```
5. Place it in your `.env` file or export it as an environment variable before launching `run_app.py`.

---

## 📸 Key Application Features

- **Sub-Second Deep Neural Inference**: MobileNetV3-Small neural network delivers high-precision predictions with 93.75% held-out test accuracy.
- **Real-Time MongoDB Logging**: Every scan is automatically logged into `crop_observations` with a unique ID (`obs_...`).
- **Comprehensive 38-Class Plant Pathology Knowledge Base**: Covers Apple, Blueberry, Cherry, Corn, Grape, Orange, Peach, Bell Pepper, Potato, Raspberry, Soybean, Squash, Strawberry, and Tomato.
- **Multimodal Agronomic Prescriptions**:
  - 🌿 **Organic & Biological Control**: Bio-fungicides, neem formulations, microbial antagonists (*Bacillus subtilis*, *Trichoderma*).
  - 🧪 **Chemical Treatment**: Approved active ingredients (FRAC group rotation, Mancozeb, Chlorothalonil, Azoxystrobin).
  - 🛡️ **Cultural & Preventative Practices**: Canopy aerating, drip irrigation, sanitization, and resistant cultivar selection.
- **Modern Botanical Web Interface**:
  - Live **MongoDB status badge** in the navigation bar.
  - Farm attribution selector linked to the MongoDB `farms` collection.
  - Drag-and-drop / file upload / camera capture with laser scan animation.
  - One-click instant test samples (Tomato Early Blight, Grape Black Rot, Citrus Greening, etc.).
  - Text-to-Speech (Web Speech API) audio prescription read-aloud for farmers in the field.
  - Printable agronomic prescription export.
  - Interactive search and filter catalog across all 38 supported diseases.

---

## 🚀 Quickstart Guide

### 1. Local Setup with Virtual Environment & MongoDB

```bash
# Clone the repository
git clone https://github.com/your-username/AgriShield-AI.git
cd AgriShield-AI

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1
# (Or on Linux/macOS: source venv/bin/activate)

# Install dependencies
pip install -r requirements.txt

# (Optional) Seed / Sync MongoDB collections
python backend/app/db/seed_db.py

# Run application
python run_app.py
```

Open your browser to:
- **Web App**: `http://localhost:8000`
- **Interactive OpenAPI Docs**: `http://localhost:8000/docs`

---

### 2. Docker Deployment

```bash
# Run backend + MongoDB with Docker Compose
docker-compose up -d --build
```

---

## 📡 MongoDB REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/db/status` | Returns MongoDB Atlas / Compass connection status and collection document counts. |
| `POST` | `/api/db/seed` | Seeds and syncs all 38 diseases in MongoDB. |
| `GET` | `/api/farms` | Returns registered farms from the `farms` collection. |
| `GET` | `/api/observations` | Retrieves all field scan observations from MongoDB `crop_observations`. |
| `POST` | `/api/predict` | Runs neural leaf classification and auto-logs diagnosis to MongoDB. |
| `POST` | `/api/predict-sample/{id}` | Runs sample leaf diagnosis and logs to MongoDB. |
| `GET` | `/api/diseases` | Retrieves disease catalog directly from MongoDB `diseases`. |
| `GET` | `/api/health` | Healthcheck returning model status, device, and MongoDB state. |

---

## 🛡️ License
Distributed under the MIT License. See `LICENSE` for details.
