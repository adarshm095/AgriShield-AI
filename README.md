# 🌿 AgriShield-AI: Smart Crop Health Doctor & Harvest Protection

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.2+-ee4c2c.svg?style=flat&logo=pytorch&logoColor=white)](https://pytorch.org)
[![MongoDB](https://img.shields.io/badge/Database-MongoDB%20Atlas%20%26%20Compass-47A248.svg?style=flat&logo=mongodb&logoColor=white)](https://www.mongodb.com)
[![Accuracy](https://img.shields.io/badge/Test%20Accuracy-93.75%25-brightgreen.svg)]()
[![Model](https://img.shields.io/badge/Architecture-MobileNetV3--Small-blue.svg)]()
[![Bilingual](https://img.shields.io/badge/Languages-English%20%7C%20%E0%A4%B9%E0%A4%BF%E0%A4%A8%E0%A5%8D%E0%A4%A6%E0%A5%80-orange.svg)]()
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)]()

**AgriShield-AI** is a farmer-first crop health diagnosis, plant pathology decision-support, and field management platform. Powered by **PyTorch MobileNetV3 Deep Learning** and persistent **MongoDB storage**, AgriShield-AI identifies **38 plant disease and healthy states across 14 major agricultural crops** with sub-second accuracy.

Designed with genuine agricultural workflows, the system provides verified **Organic Remedies (देसी उपाय)**, **Chemical Spray Guidelines (दवा छिड़काव)**, an interactive **AI Agronomist Doctor Copilot**, and dynamic **Field & Plot Tracking**.

---

## 🍃 Key Features & Architecture

### 1. Farmer-First Botanical Design & Multilingual Support
- **Clean Botanical Interface**: Built with an earthy, modern agricultural aesthetic replacing generic cyberpunk clichés.
- **English & Hindi (`हिन्दी`) Language Toggle**: One-click switch translating labels, diagnoses, and advisory tips for maximum farmer accessibility.
- **Accessible & Practical Terminology**: Uses simple language like *"Crop Health Doctor"*, *"Diagnose Leaf"*, *"Organic Remedies"*, and *"Spray Guide"*.

### 2. User Authentication & Farmer Profiles (`users` Collection)
- **Account Registration & Login**: Farmers can sign up with Name, Email/Phone, Village/Location, and Password.
- **Secure Password Hashing**: PBKDF2-HMAC-SHA256 cryptography with unique cryptographic salts.
- **Session Tokens**: Authenticated sessions allow farmers to access their own private field plots and scan history.

### 3. Dynamic Field & Plot Management (`farms` Collection)
- **Custom Field Creation**: Farmers can register their own fields with Field Name, Crop Type, Land Area (in Acres), Sowing Date, and Location.
- **Dynamic Field Selector**: The Leaf Scanner automatically populates with the farmer's active fields, with a quick `+ New Field` registration modal right inside the scanner.

### 4. High-Accuracy Plant Disease Diagnostics
- **MobileNetV3 Neural Network**: Compact and fast computer vision model (93.75% test accuracy) capable of real-time classification.
- **38 Disease Classes across 14 Crops**: Apple, Blueberry, Cherry, Corn, Grape, Orange, Peach, Bell Pepper, Potato, Raspberry, Soybean, Squash, Strawberry, and Tomato.
- **Auto-Persistent Field Health Logs (`crop_observations`)**: Scans are logged with severity, risk level, symptoms, and remedies under the selected field.

### 5. Interactive AI Agronomist Copilot (`/api/ai/advisor`)
- **Conversational Expert Advice**: Farmers can ask specific follow-up questions (*"What is the exact dosage per acre?"*, *"Can I spray Neem oil today?"*, *"How many days before harvest?"*).
- **Dual Engine**: Connects to **Google Gemini API** when configured in `.env`, or utilizes a specialized agricultural reasoning engine for immediate English & Hindi recommendations.

---

## 🗄️ Database Schema (`agrishield_db`)

| Collection | Purpose | Key Indexed Fields |
| :--- | :--- | :--- |
| **`users`** | Farmer profiles and encrypted credentials | `_id`, `name`, `email` (unique), `phone`, `password_hash`, `salt`, `role`, `location` |
| **`farms`** | Individual crop fields and plots | `_id`, `farmName`, `crop`, `area` (acres), `farmerId`, `farmerName`, `location`, `sowingDate` |
| **`crop_observations`** | Field scan diagnosis logs | `_id`, `farmId`, `farmerId`, `crop`, `prediction`, `riskLevel`, `createdAt` |
| **`diseases`** | 38 plant pathology profiles & treatment database | `name`, `crop`, `class_name`, `pathogen_type`, `organic_treatment`, `chemical_treatment`, `prevention` |

---

## 🚀 Quickstart Guide

### 1. Local Setup with Virtual Environment

```bash
# Clone the repository
git clone https://github.com/your-username/AgriShield-AI.git
cd AgriShield-AI

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1
# (Or on Linux/macOS: source venv/bin/activate)

# Install requirements
pip install -r requirements.txt

# (Optional) Seed / Sync database
python backend/app/db/seed_db.py

# Launch application
python run_app.py
```

Open your browser to:
- **Application Dashboard**: `http://localhost:8000`
- **Interactive OpenAPI Docs**: `http://localhost:8000/docs`

---

### 2. Environment Configuration (`.env`)

```env
# Local MongoDB (Default):
MONGODB_URI=mongodb://localhost:27017/agrishield_db

# Or MongoDB Atlas (Cloud Cluster):
# MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/agrishield_db?retryWrites=true&w=majority

# Optional: Google Gemini API Key for Live AI Agronomist Copilot:
# GEMINI_API_KEY=your_key_here

PORT=8000
HOST=0.0.0.0
```

---

## 📡 REST API Reference

### Authentication & Users
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Register a new farmer account & create starter field. |
| `POST` | `/api/auth/login` | Authenticate farmer with email/phone & password. |
| `GET` | `/api/auth/me` | Fetch active user profile from session token. |

### Dynamic Fields & Farms
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/farms` | List registered fields (filtered by `farmer_id`). |
| `POST` | `/api/farms` | Register a new field/plot under the current farmer. |

### Crop Health Diagnostics & AI Advisor
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/predict` | Upload leaf image; classifies disease & logs observation. |
| `POST` | `/api/predict-sample/{id}` | Run diagnosis on pre-loaded test leaf sample. |
| `POST` | `/api/ai/advisor` | Interactive AI Agronomist Copilot consultation (EN/HI). |
| `GET` | `/api/observations` | Retrieve field health inspection logs. |
| `DELETE` | `/api/observations/{id}` | Delete a past scan record. |

### Pathology Encyclopedia & System
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/diseases` | List 38 disease conditions with filters (crop, pathogen). |
| `GET` | `/api/diseases/{class_name}` | Detailed symptoms, organic & spray remedies for condition. |
| `GET` | `/api/crops` | List supported crops and associated disease conditions. |
| `GET` | `/api/health` | Service healthcheck & model status. |

---

## 🛡️ License
Distributed under the MIT License. See `LICENSE` for details.
