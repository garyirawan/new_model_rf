
import os
import sys
from typing import Optional, Dict, Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# pastikan inference_rf.py bisa diimport (dalam folder yang sama)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(HERE)

from inference_rf import RFRegressorWrapper, decide_potability, Thresholds, status_badges

# Lokasi model & urutan fitur (menggunakan model terbaru yang sudah improved)
MODEL_PATH = os.getenv("MODEL_PATH", os.path.join(HERE, "rf_total_coliform_log1p_improved.joblib"))
FEATURES_ORDER_PATH = os.getenv("FEATURES_ORDER_PATH", os.path.join(HERE, "model_features_order.txt"))

# Inisialisasi app & model sekali di startup
app = FastAPI(title="Water Quality AI API", version="1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rfw = None
@app.on_event("startup")
def _load_model():
    global rfw
    rfw = RFRegressorWrapper(MODEL_PATH, FEATURES_ORDER_PATH)
    print(f"✓ Model loaded successfully from {MODEL_PATH}")

class PredictRequest(BaseModel):
    temp_c: float = Field(..., description="Temperature in °C")
    do_mgl: float = Field(..., description="Dissolved Oxygen in mg/L")
    ph: float = Field(..., description="pH")
    conductivity_uscm: float = Field(..., description="Conductivity in µS/cm")
    totalcoliform_mpn_100ml: Optional[float] = Field(None, description="Measured Total Coliform (MPN/100mL), optional")

class ThresholdRequest(BaseModel):
    total_coliform_max_mpn_100ml: float = 0.0
    ph_min: float = 6.5
    ph_max: float = 8.5
    conductivity_max_uscm: float = 1500.0
    do_min_info_mgl: float = 5.0

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/predict")
def predict(req: PredictRequest):
    # Use default thresholds
    th = ThresholdRequest()
    
    # 1) Prediksi mikroba (proxy) dari 4 fitur
    features = {
        "temp_c": float(req.temp_c),
        "do_mgl": float(req.do_mgl),
        "ph": float(req.ph),
        "conductivity_uscm": float(req.conductivity_uscm),
    }
    infer = rfw.predict_with_interval(features)

    # 2) Keputusan potabilitas (rules)
    readings = dict(features)
    if req.totalcoliform_mpn_100ml is not None:
        readings["totalcoliform_mpn_100ml"] = float(req.totalcoliform_mpn_100ml)

    thresholds = Thresholds(**th.dict())
    decision = decide_potability(readings, infer.pred_total_coliform_mpn_100ml, thresholds)

    # 3) Badge status per parameter
    badges = status_badges(readings, thresholds)

    # 4) Response
    return {
        "input_used": infer.used_input,
        "prediction": {
            "total_coliform_mpn_100ml": infer.pred_total_coliform_mpn_100ml,
            "ci90_low": infer.pred_ci90_low,
            "ci90_high": infer.pred_ci90_high,
            "disclaimer": "Estimasi AI berbasis 4 parameter fisiko-kimia (bukan hasil uji lab)."
        },
        "ai_detection": {
            "potable": decision.potable,
            "reasons": decision.reasons,
            "recommendations": decision.recommendations,
            "alternative_use": decision.alternative_use,
            "thresholds": th.dict()
        },
        "status_badges": badges
    }
