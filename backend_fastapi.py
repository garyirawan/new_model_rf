
import os
import sys
from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from collections import deque

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

# In-memory storage untuk data IoT (max 1000 data points)
iot_data_storage = deque(maxlen=1000)

rfw = None
@app.on_event("startup")
def _load_model():
    global rfw
    rfw = RFRegressorWrapper(MODEL_PATH, FEATURES_ORDER_PATH)
    print(f"✓ Model loaded successfully from {MODEL_PATH}")

# ====== DATA MODELS ======

class IoTDataInput(BaseModel):
    """Data dari ESP32/Mappi32"""
    temp_c: float = Field(..., description="Temperature in °C", example=27.8)
    do_mgl: float = Field(..., description="Dissolved Oxygen in mg/L", example=6.2)
    ph: float = Field(..., description="pH", example=7.2)
    conductivity_uscm: float = Field(..., description="Conductivity in µS/cm", example=620)
    totalcoliform_mv: Optional[float] = Field(None, description="Total Coliform sensor reading in mV (optional)")

class PredictRequest(BaseModel):
    temp_c: float = Field(..., description="Temperature in °C")
    do_mgl: float = Field(..., description="Dissolved Oxygen in mg/L")
    ph: float = Field(..., description="pH")
    conductivity_uscm: float = Field(..., description="Conductivity in µS/cm")
    totalcoliform_mpn_100ml: Optional[float] = Field(None, description="Measured Total Coliform (MPN/100mL), optional")

class ThresholdRequest(BaseModel):
    # Updated Nov 6, 2025 - Sistem 3 Tingkatan
    # Total Coliform: Aman ≤0.70 | Waspada 0.70-0.99 | Bahaya ≥1.0
    total_coliform_safe_mpn_100ml: float = 0.70
    total_coliform_warning_mpn_100ml: float = 1.0
    
    # Suhu: Aman 10-35°C | Waspada 36-44°C (E. coli) | Aman tapi panas ≥45°C
    temp_safe_min_c: float = 10.0
    temp_safe_max_c: float = 35.0
    temp_warning_min_c: float = 36.0
    temp_warning_max_c: float = 44.0
    temp_hot_safe_c: float = 45.0
    
    # pH: Permenkes 2023
    ph_min: float = 6.5
    ph_max: float = 8.5
    
    # Konduktivitas: EPA Amerika
    conductivity_max_uscm: float = 1000.0
    
    # DO: Aman ≥6 | Rendah 5-6 | Waspada <5
    do_optimal_mgl: float = 6.0
    do_low_mgl: float = 5.0

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
    # Tambahkan prediksi coliform ke readings untuk badge (jika tidak ada nilai terukur)
    readings_for_badge = dict(readings)
    if "totalcoliform_mpn_100ml" not in readings_for_badge:
        readings_for_badge["totalcoliform_mpn_100ml"] = infer.pred_total_coliform_mpn_100ml
    badges = status_badges(readings_for_badge, thresholds)

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
            "severity": decision.severity,  # NEW: Tambahkan severity untuk frontend
            "reasons": decision.reasons,
            "recommendations": decision.recommendations,
            "alternative_use": decision.alternative_use,
            "thresholds": th.dict()
        },
        "status_badges": badges
    }

# ====== IoT ENDPOINTS ======

def convert_mv_to_mpn(mv_value: Optional[float]) -> Optional[float]:
    """
    Konversi nilai sensor Total Coliform dari mV ke MPN/100mL
    
    Berdasarkan kalibrasi sensor fiber optik:
    - 0 mV = 0 MPN/100mL (tidak ada bakteri)
    - 1000 mV = 10 MPN/100mL (kontaminasi tinggi)
    
    Formula linear: MPN/100mL = (mV / 1000) * 10
    Simplified: MPN/100mL = mV / 100
    """
    if mv_value is None:
        return None
    
    # Formula konversi: mV / 100
    mpn_100ml = mv_value / 100.0
    
    # Batasi nilai minimum ke 0 (tidak boleh negatif)
    return max(0.0, mpn_100ml)

@app.post("/iot/data")
def receive_iot_data(data: IoTDataInput):
    """
    Endpoint untuk menerima data dari ESP32/Mappi32
    
    ESP32 akan POST data sensor ke endpoint ini.
    Data akan disimpan di memory dan bisa diambil via /iot/latest
    """
    try:
        # Konversi sensor mV ke MPN/100mL
        totalcoliform_mpn = convert_mv_to_mpn(data.totalcoliform_mv)
        
        # Simpan data dengan timestamp
        iot_record = {
            "timestamp": datetime.now().isoformat(),
            "temp_c": data.temp_c,
            "do_mgl": data.do_mgl,
            "ph": data.ph,
            "conductivity_uscm": data.conductivity_uscm,
            "totalcoliform_mv": data.totalcoliform_mv,
            "totalcoliform_mpn_100ml": totalcoliform_mpn
        }
        
        iot_data_storage.append(iot_record)
        
        return {
            "status": "success",
            "message": "Data received from IoT device",
            "data": iot_record,
            "total_records": len(iot_data_storage)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/iot/latest")
def get_latest_iot_data():
    """
    Endpoint untuk mendapatkan data IoT terbaru dengan badge status
    
    Frontend akan polling endpoint ini untuk mendapatkan data real-time
    Badge akan menunjukkan status untuk setiap parameter termasuk Total Coliform sensor
    """
    if len(iot_data_storage) == 0:
        return {
            "status": "no_data",
            "message": "No IoT data available yet",
            "data": None
        }
    
    latest = iot_data_storage[-1]
    
    # Generate badges untuk semua parameter termasuk coliform sensor
    # Gunakan default thresholds
    th = Thresholds()
    
    # Buat dictionary untuk badge calculation (gunakan nilai MPN/100mL untuk coliform)
    readings_for_badge = {
        "temp_c": latest.get("temp_c"),
        "do_mgl": latest.get("do_mgl"),
        "ph": latest.get("ph"),
        "conductivity_uscm": latest.get("conductivity_uscm"),
        "totalcoliform_mpn_100ml": latest.get("totalcoliform_mpn_100ml")  # Gunakan nilai terkonversi
    }
    
    badges = status_badges(readings_for_badge, th)
    
    return {
        "status": "success",
        "data": latest,
        "badges": badges,
        "total_records": len(iot_data_storage)
    }

@app.get("/iot/history")
def get_iot_history(limit: int = 50):
    """
    Endpoint untuk mendapatkan history data IoT
    
    Parameter:
    - limit: jumlah data terbaru yang diambil (default 50)
    """
    if len(iot_data_storage) == 0:
        return {
            "status": "no_data",
            "message": "No IoT data available yet",
            "data": []
        }
    
    # Ambil data terbaru sebanyak limit
    history = list(iot_data_storage)[-limit:]
    
    return {
        "status": "success",
        "data": history,
        "count": len(history),
        "total_records": len(iot_data_storage)
    }

@app.post("/iot/predict")
def predict_from_iot():
    """
    Endpoint untuk auto-predict dari data IoT terbaru
    
    Akan otomatis mengambil data IoT terbaru dan melakukan prediksi
    """
    if len(iot_data_storage) == 0:
        raise HTTPException(status_code=404, detail="No IoT data available")
    
    latest = iot_data_storage[-1]
    
    # Convert ke PredictRequest
    req = PredictRequest(
        temp_c=latest["temp_c"],
        do_mgl=latest["do_mgl"],
        ph=latest["ph"],
        conductivity_uscm=latest["conductivity_uscm"],
        totalcoliform_mpn_100ml=None
    )
    
    # Gunakan endpoint predict yang sudah ada
    result = predict(req)
    
    # Tambahkan info IoT
    result["iot_timestamp"] = latest["timestamp"]
    result["iot_source"] = "mappi32"
    
    return result

@app.delete("/iot/clear")
def clear_iot_data():
    """
    Endpoint untuk clear semua data IoT (untuk testing)
    """
    iot_data_storage.clear()
    return {
        "status": "success",
        "message": "All IoT data cleared"
    }
