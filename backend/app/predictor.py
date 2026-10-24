import os
import sys

# Add ml folder to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
sys.path.append(os.path.join(PROJECT_ROOT, "ml"))

from inference import PlantDiseasePredictor

_predictor_instance = None

def get_predictor():
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = PlantDiseasePredictor()
    return _predictor_instance
