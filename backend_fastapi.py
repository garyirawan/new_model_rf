
import os
import sys
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from collections import deque
import time

# pastikan inference_rf.py bisa diimport (dalam folder yang sama)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(HERE)

from inference_rf import RFRegressorWrapper, decide_potability, Thresholds, status_badges

# ========================================
# SENSOR IDs CONFIGURATION (Hardcoded)
# ========================================
SENSOR_IDS = {
    "ph_temp": "PH_TEMP_SLAVE_ID",      # pH & Temperature sensor (combined)
    "do": "DO_SLAVE_ID",                 # Dissolved Oxygen sensor
    "conductivity": "EC_SLAVE_ID",       # Electrical Conductivity sensor
    "totalcoliform": "ECOLI_SLAVE_ID"    # E.Coli Fiber Optic sensor
}

# ========================================
# TIMEZONE CONFIGURATION (WIB/UTC+7)
# ========================================
WIB = timezone(timedelta(hours=7))  # WIB = UTC+7

# ========================================
# LOGGING CONFIGURATION WITH WIB TIMEZONE
# ========================================
class WIBFormatter(logging.Formatter):
    """Custom formatter dengan timezone WIB"""
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=WIB)
        if datefmt:
            return dt.strftime(datefmt)
        else:
            return dt.strftime('%Y-%m-%d %H:%M:%S %Z')

# Setup logging
def setup_logger():
    """Setup logger dengan file dan console handler"""
    logger = logging.getLogger("water_quality_api")
    logger.setLevel(logging.INFO)
    
    # Hindari duplicate handlers
    if logger.handlers:
        return logger
    
    # Format log dengan timestamp WIB
    log_format = '%(asctime)s [%(levelname)s] %(name)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Console Handler (untuk development & Hugging Face logs)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = WIBFormatter(log_format, datefmt=date_format)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File Handler (untuk persistent logs di Hugging Face Spaces)
    try:
        log_dir = os.path.join(HERE, "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "water_quality_api.log")
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_formatter = WIBFormatter(log_format, datefmt=date_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        logger.info(f"Log file created: {log_file}")
    except Exception as e:
        logger.warning(f"Could not create log file: {e}")
    
    return logger

# Initialize logger
logger = setup_logger()

# Lokasi model & urutan fitur (menggunakan model terbaru yang sudah improved)
MODEL_PATH = os.getenv("MODEL_PATH", os.path.join(HERE, "rf_total_coliform_log1p_improved.joblib"))
FEATURES_ORDER_PATH = os.getenv("FEATURES_ORDER_PATH", os.path.join(HERE, "model_features_order.txt"))

# Inisialisasi app & model sekali di startup
app = FastAPI(
    title="Water Quality AI Monitoring API",
    description="""
    🚰 API untuk Monitoring Kualitas Air Berbasis AI dan IoT
    
    API ini menyediakan layanan prediksi kualitas air menggunakan Machine Learning (Random Forest) 
    dan integrasi dengan sensor IoT (ESP32/Mappi32) untuk monitoring real-time.
    
    ## Fitur Utama:
    
    * AI Prediction: Prediksi Total Coliform (MPN/100mL) dari parameter fisiko-kimia
    * IoT Integration: Menerima dan menyimpan data dari sensor real-time
    * 3-Tier Severity System: Klasifikasi kualitas air (Aman/Waspada/Bahaya)
    * Status Badges: Badge berwarna untuk setiap parameter air
    * History Storage: Penyimpanan data historis (in-memory, max 1000 records)
    
    ## Data Flow:
    
    1. Hardware → API ESP32 POST data sensor ke `/iot/data`
    2. API → Storage Data disimpan di in-memory deque (maxlen=1000)
    3. Frontend → API Dashboard polling `/iot/latest` dan `/iot/history`
    4. AI Processing `/predict` atau `/iot/predict` untuk analisis kualitas air
    
    ## Parameter Air yang Dimonitor:
    
    - Temperature (°C): 10-35°C (optimal)
    - Dissolved Oxygen (mg/L): ≥6 mg/L (layak)
    - pH 6.5-8.5 (netral)
    - Conductivity (μS/cm): 0-1000 μS/cm (normal)
    - Total Coliform (MPN/100mL): <1 MPN/100mL (aman)
    
    ## Threshold Sistem 3-Tier:

    - 🟢 Safe (Aman): Semua parameter dalam batas aman (Dengan prediksi MPN berada di angka ≤0.70 MPN/100ml)
    - 🟡 Warning (Waspada): Satu atau lebih parameter di zona waspada (Dengan prediksi MPN berada di angka  0.71-0.99 MPN/100ml)
    - 🔴 Danger (Bahaya): Parameter kritis melewati batas ambang waspada (Dengan prediksi MPN berada di angka  ≥1.0 MPN/100ml)
    """,
    version="2.0.0",
    contact={
        "name": "Water Quality AI Team",
        "url": "https://github.com/garyirawan/new_model_rf",
    },
    license_info={
        "name": "",
    },
    tags_metadata=[
        {
            "name": "System",
            "description": "Health check dan monitoring sistem API",
        },
        {
            "name": "AI Prediction",
            "description": "Endpoint untuk prediksi kualitas air menggunakan Machine Learning",
        },
        {
            "name": "IoT Data Management",
            "description": "Endpoint untuk integrasi dengan sensor IoT (ESP32/Mappi32)",
        },
    ]
)

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

# ========================================
# MIDDLEWARE FOR REQUEST LOGGING
# ========================================
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log setiap HTTP request dengan timestamp WIB"""
    start_time = time.time()
    
    # Log incoming request
    logger.info(f"→ {request.method} {request.url.path} | Client: {request.client.host if request.client else 'unknown'}")
    
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Log response
        logger.info(f"← {request.method} {request.url.path} | Status: {response.status_code} | Time: {process_time:.2f}ms")
        
        return response
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        logger.error(f"✗ {request.method} {request.url.path} | Error: {str(e)} | Time: {process_time:.2f}ms")
        raise

# ========================================
# STARTUP & SHUTDOWN EVENTS
# ========================================
rfw = None

@app.on_event("startup")
def _load_model():
    """Load ML model saat aplikasi startup"""
    global rfw
    
    logger.info("="*60)
    logger.info("🚀 WATER QUALITY API STARTING UP")
    logger.info("="*60)
    logger.info(f"Model path: {MODEL_PATH}")
    logger.info(f"Features order path: {FEATURES_ORDER_PATH}")
    logger.info(f"Timezone: WIB (UTC+7)")
    
    try:
        rfw = RFRegressorWrapper(MODEL_PATH, FEATURES_ORDER_PATH)
        logger.info("✓ Model loaded successfully")
        logger.info(f"✓ Model type: Random Forest Regressor")
        logger.info(f"✓ Expected features: {rfw.expected_features if hasattr(rfw, 'expected_features') else 'N/A'}")
    except Exception as e:
        logger.error(f"✗ Failed to load model: {str(e)}")
        raise
    
    logger.info("="*60)
    logger.info("✓ API READY - Listening for requests")
    logger.info("="*60)

@app.on_event("shutdown")
def _shutdown():
    """Cleanup saat aplikasi shutdown"""
    logger.info("="*60)
    logger.info("🛑 WATER QUALITY API SHUTTING DOWN")
    logger.info(f"Total data stored: {len(iot_data_storage)} records")
    logger.info("="*60)

# ====== DATA MODELS ======

class IoTDataInput(BaseModel):
    """
    Schema untuk data dari ESP32/Mappi32 sensor IoT.
    
    Data sensor dikirim via POST ke endpoint `/iot/data`.
    Total Coliform dalam bentuk mV akan otomatis dikonversi ke MPN/100mL.
    
    **Sensor IDs (Hardcoded di Backend)**:
    - PH_TEMP_SLAVE_ID: pH & Temperature sensor (combined)
    - DO_SLAVE_ID: Dissolved Oxygen sensor
    - EC_SLAVE_ID: Electrical Conductivity sensor
    - ECOLI_SLAVE_ID: E.Coli Fiber Optic sensor
    
    **Formula konversi**: MPN/100mL = mV / 100
    
    **Rentang Normal**:
    - Temperature: 20-30°C
    - DO: 6-8 mg/L
    - pH: 6.5-8.5
    - Conductivity: 50-1500 μS/cm
    - Total Coliform mV: 0-1000 mV (0-10 MPN/100mL setelah konversi)
    """
    temp_c: float = Field(..., description="Temperature in °C", example=27.8)
    do_mgl: float = Field(..., description="Dissolved Oxygen in mg/L", example=6.2)
    ph: float = Field(..., description="pH level", example=7.2)
    conductivity_uscm: float = Field(..., description="Conductivity in µS/cm", example=620)
    totalcoliform_mv_raw: Optional[float] = Field(None, description="Total Coliform raw sensor reading in mV (raw voltage from sensor)", example=50.0)

class PredictRequest(BaseModel):
    """
    Schema untuk request prediksi kualitas air menggunakan AI.
    
    Endpoint `/predict` menerima 4 parameter wajib (fisiko-kimia) dan 1 parameter opsional.
    Model AI akan memprediksi Total Coliform jika tidak disediakan.
    
    **Use Case**:
    - **Prediksi penuh**: Kirim 4 parameter → AI prediksi Total Coliform
    - **Validasi sensor**: Kirim 4 parameter + totalcoliform_mv → AI bandingkan dengan pengukuran aktual
    
    **Parameter Wajib**:
    - Temperature, DO, pH, Conductivity
    
    **Parameter Opsional**:
    - Total Coliform (MPN/100mL) dari sensor atau lab test
    """
    temp_c: float = Field(..., description="Temperature in °C", example=27.8)
    do_mgl: float = Field(..., description="Dissolved Oxygen in mg/L", example=6.2)
    ph: float = Field(..., description="pH level", example=7.2)
    conductivity_uscm: float = Field(..., description="Conductivity in µS/cm", example=620)
    totalcoliform_mv: Optional[float] = Field(None, description="Measured Total Coliform (MPN/100mL) - optional, akan diprediksi jika tidak ada", example=0.5)

class ThresholdRequest(BaseModel):
    """
    Schema untuk konfigurasi threshold sistem 3-tier.
    
    **Sistem 3-Tier** (Updated Nov 8, 2025):
    - 🟢 **Safe (Aman)**: Total Coliform ≤ 0.70 MPN/100mL
    - 🟡 **Warning (Waspada)**: Total Coliform 0.71 - 0.99 MPN/100mL
    - 🔴 **Danger (Bahaya)**: Total Coliform ≥ 1.0 MPN/100mL
    
    **Threshold untuk parameter lain**:
    - Temperature: <20°C atau >30°C (Warning), <15°C atau >35°C (Danger)
    - DO: <6 mg/L (Warning), <4 mg/L (Danger)
    - pH: <6.5 atau >8.5 (Warning), <6.0 atau >9.0 (Danger)
    - Conductivity: <50 atau >1500 μS/cm (Warning), <30 atau >2000 μS/cm (Danger)
    """
    # Total Coliform: Aman ≤0.70 | Waspada 0.71-0.99 | Bahaya ≥1.0
    total_coliform_safe_mpn_100ml: float = 0.70
    total_coliform_danger_mpn_100ml: float = 1.0
    
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

@app.get(
    "/health",
    tags=["System"],
    summary="Health Check",
    response_description="Status sistem API"
)
def health():
    """
    ## Health Check Endpoint
    
    Endpoint untuk mengecek status sistem API.
    
    **Use Case**:
    - Monitoring uptime sistem
    - Load balancer health check
    - CI/CD deployment verification
    
    **Response**:
    ```json
    {
        "status": "ok"
    }
    ```
    
    **Status Codes**:
    - `200 OK`: API berjalan normal
    """
    logger.info("Health check request received")
    return {"status": "ok"}

@app.post(
    "/predict",
    tags=["AI Prediction"],
    summary="Prediksi Kualitas Air dengan AI (Manual Input)",
    response_description="Hasil prediksi AI dengan analisis kelayakan air"
)
def predict(req: PredictRequest):
    """
    ## AI Water Quality Prediction (Manual Input)
    
    Endpoint untuk prediksi kualitas air dengan **INPUT MANUAL** dari user.
    
    ---
    
    ### 🔀 **Perbedaan `/predict` vs `/iot/predict`:**
    
    | Aspek | `/predict` (Endpoint ini) | `/iot/predict` |
    |-------|---------------------------|----------------|
    | **Input** | ✅ Manual (kirim parameter) | ❌ Auto (ambil dari sensor) |
    | **Request Body** | ✅ Required | ❌ Empty |
    | **Use Case** | Testing, simulasi, lab validation | Real-time monitoring, automation |
    | **User** | Human (researcher, technician) | Machine (scheduler, automation) |
    
    ### ✅ **Kapan Pakai `/predict` (Endpoint Ini):**
    - 🧪 **Testing & Simulasi**: Coba berbagai skenario parameter "what-if"
    - 📝 **Manual Input**: User input langsung dari web form/dashboard
    - 🔬 **Lab Validation**: Bandingkan hasil lab test dengan prediksi AI
    - 💻 **API Integration**: Testing untuk aplikasi eksternal
    - 📊 **Research**: Analisis parameter untuk riset kualitas air
    
    ### ❌ **Jangan Pakai `/predict` Jika:**
    - Data sudah ada di sensor IoT → Pakai `/iot/predict` (lebih mudah, 1 API call)
    - Butuh automation periodik → Pakai `/iot/predict` (no input needed)
    
    ---
    
    **Fitur**:
    - Prediksi Total Coliform (MPN/100mL) dari 4 parameter fisiko-kimia
    - Analisis kelayakan air dengan sistem 3-tier (Safe/Warning/Danger)
    - Status badge untuk setiap parameter
    - Confidence interval 90% untuk prediksi
    - Rekomendasi tindakan berdasarkan kualitas air
    
    **Input Parameters (WAJIB kirim via request body)**:
    - `temp_c`: Suhu air (°C) - Contoh: 27.8
    - `do_mgl`: Dissolved Oxygen (mg/L) - Contoh: 6.2
    - `ph`: pH level - Contoh: 7.2
    - `conductivity_uscm`: Konduktivitas (µS/cm) - Contoh: 620
    
    **Response Structure**:
    ```json
    {
        "input_used": {
            "temp_c": 27.8,
            "do_mgl": 6.2,
            "ph": 7.2,
            "conductivity_uscm": 620
        },
        "ai_detection": {
            "potable": true,
            "severity": "safe",
            "reasons": [],
            "recommendations": [],
            "alternative_use": null,
            "thresholds": {...}
        },
        "status_badges": {
            "temp_c": {"status": "safe", "color": "green", "label": "Normal"},
            "do_mgl": {"status": "safe", "color": "green", "label": "Optimal"}
        }
    }
    ```
    
    **Severity Levels**:
    - `safe`: Semua parameter aman (air layak minum)
    - `warning`: Ada parameter di zona peringatan (perlu monitoring)
    - `danger`: Parameter kritis berbahaya (air tidak layak)
    
    **Example Request**:
    ```bash
    curl -X POST "http://localhost:8000/predict" \\
         -H "Content-Type: application/json" \\
         -d '{
           "temp_c": 27.8,
           "do_mgl": 6.2,
           "ph": 7.2,
           "conductivity_uscm": 620
         }'
    ```
    
    **Status Codes**:
    - `200 OK`: Prediksi berhasil
    - `422 Validation Error`: Parameter tidak valid
    - `500 Internal Server Error`: Error pada model AI
    """
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
    if req.totalcoliform_mv is not None:
        readings["totalcoliform_mv"] = float(req.totalcoliform_mv)

    thresholds = Thresholds(**th.dict())
    decision = decide_potability(readings, infer.pred_total_coliform_mv, thresholds)

    # 3) Badge status per parameter
    # Badge SEMUA parameter (termasuk Total Coliform) ikut nilai ASLI dari sensor/readings
    # Badge Total Coliform ikut SENSOR (bukan prediksi AI)
    readings_for_badge = dict(readings)
    badges = status_badges(readings_for_badge, thresholds)
    
    # Log prediction
    logger.info(f"AI Prediction: temp={req.temp_c}°C, DO={req.do_mgl}mg/L, pH={req.ph}, cond={req.conductivity_uscm}µS/cm → Coliform={infer.pred_total_coliform_mv:.3f} MPN/100mL | Severity={decision.severity} | Potable={decision.potable}")

    # 4) Response
    return {
        "input_used": infer.used_input,
        "prediction": {
            "total_coliform_mv": infer.pred_total_coliform_mv,
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

@app.post(
    "/iot/data",
    tags=["IoT Data Management"],
    summary="Terima Data dari Sensor IoT",
    response_description="Konfirmasi penerimaan data dan total records"
)
def receive_iot_data(data: IoTDataInput):
    """
    ## IoT Data Ingestion Endpoint
    
    Endpoint untuk menerima data real-time dari ESP32/Mappi32 sensor.
    
    **Hardware Integration**:
    - ESP32 via LoRa/WiFi POST data sensor ke endpoint ini
    - Data disimpan di in-memory deque (maxlen=1000)
    - Konversi otomatis sensor mV_raw → MPN/100mL
    - Timestamp ditambahkan otomatis (WIB/UTC+7)
    - **Sensor IDs didefinisikan di backend** (tidak perlu dikirim dari IoT device)
    
    **Sensor Mapping (Hardcoded)**:
    - `temp_c` & `ph` → **PH_TEMP_SLAVE_ID** (sensor gabungan)
    - `do_mgl` → **DO_SLAVE_ID**
    - `conductivity_uscm` → **EC_SLAVE_ID**
    - `totalcoliform_mv_raw` → **ECOLI_SLAVE_ID**
    
    **Input Data (Request Body)**:
    - `temp_c`: Suhu air (°C) - **Required**
    - `do_mgl`: Dissolved Oxygen (mg/L) - **Required**
    - `ph`: pH level - **Required**
    - `conductivity_uscm`: Konduktivitas (µS/cm) - **Required**
    - `totalcoliform_mv_raw`: Sensor Total Coliform dalam mV - **Optional**
    
    **Konversi Sensor**:
    - Formula: `MPN/100mL = mV_raw / 100`
    - Contoh: 50 mV → 0.5 MPN/100mL
    - Range: 0-1000 mV → 0-10 MPN/100mL
    
    **Response Example**:
    ```json
    {
        "status": "success",
        "message": "Data received from IoT device",
        "data": {
            "timestamp": "2025-11-09T14:30:00",
            "sensor_ids": {
                "ph_temp": "PH_TEMP_SLAVE_ID",
                "do": "DO_SLAVE_ID",
                "conductivity": "EC_SLAVE_ID",
                "totalcoliform": "ECOLI_SLAVE_ID"
            },
            "temp_c": 27.8,
            "do_mgl": 6.2,
            "ph": 7.2,
            "conductivity_uscm": 620,
            "totalcoliform_mv_raw": 50.0,
            "totalcoliform_mv": 0.5
        },
        "total_records": 42
    }
    ```
    
    **Storage**:
    - In-memory (non-persistent)
    - Max 1000 data points (FIFO queue)
    - Data hilang saat restart server
    
    **ESP32 Example Code**:
    ```cpp
    HTTPClient http;
    http.begin("http://api-url/iot/data");
    http.addHeader("Content-Type", "application/json");
    
    // Sensor IDs otomatis ditambahkan oleh backend, tidak perlu dikirim
    String payload = "{\\"temp_c\\":27.8,\\"do_mgl\\":6.2,\\"ph\\":7.2,\\"conductivity_uscm\\":620,\\"totalcoliform_mv_raw\\":50.0}";
    int httpCode = http.POST(payload);
    ```
    
    **Status Codes**:
    - `200 OK`: Data berhasil disimpan
    - `422 Validation Error`: Format data tidak valid
    - `500 Internal Server Error`: Error penyimpanan data
    """
    try:
        # Konversi sensor mV ke MPN/100mL (input field is raw mV)
        totalcoliform_mpn = convert_mv_to_mpn(data.totalcoliform_mv_raw)

        # Format coliform value untuk logging
        coliform_display = f"{totalcoliform_mpn:.3f}" if totalcoliform_mpn is not None else "N/A"

        # Log incoming IoT data
        logger.info(f"📡 IoT Data received: temp={data.temp_c}°C, DO={data.do_mgl}mg/L, pH={data.ph}, cond={data.conductivity_uscm}µS/cm, coliform_mv_raw={data.totalcoliform_mv_raw}mV → {coliform_display} MPN/100mL")

        # Simpan data dengan timestamp WIB dan sensor IDs (dari config backend)
        iot_record = {
            "timestamp": datetime.now(WIB).isoformat(),  # Timestamp dengan WIB timezone
            "sensor_ids": SENSOR_IDS,  # Tambahkan sensor IDs dari config backend
            "temp_c": data.temp_c,
            "do_mgl": data.do_mgl,
            "ph": data.ph,
            "conductivity_uscm": data.conductivity_uscm,
            "totalcoliform_mv_raw": data.totalcoliform_mv_raw,
            "totalcoliform_mv": totalcoliform_mpn
        }

        iot_data_storage.append(iot_record)

        logger.info(f"✓ IoT data stored successfully. Total records: {len(iot_data_storage)}")

        return {
            "status": "success",
            "message": "Data received from IoT device",
            "data": iot_record,
            "total_records": len(iot_data_storage)
        }
    except Exception as e:
        logger.error(f"✗ Failed to store IoT data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get(
    "/iot/latest",
    tags=["IoT Data Management"],
    summary="Dapatkan Data Sensor Terbaru",
    response_description="Data sensor terbaru dengan status badges"
)
def get_latest_iot_data():
    """
    ## Latest IoT Data Endpoint
    
    Endpoint untuk mendapatkan data sensor IoT terbaru dengan status badges.
    
    **Use Case**:
    - Frontend dashboard polling setiap 1 jam
    - Real-time monitoring display
    - Status badge untuk semua parameter
    
    **Response Structure**:
    ```json
    {
        "status": "success",
        "data": {
            "timestamp": "2025-11-07T14:30:00",
            "sensor_ids": {
                "ph_temp": "PH_TEMP_SLAVE_ID",
                "do": "DO_SLAVE_ID",
                "conductivity": "EC_SLAVE_ID",
                "totalcoliform": "ECOLI_SLAVE_ID"
            },
            "temp_c": 27.8,
            "do_mgl": 6.2,
            "ph": 7.2,
            "conductivity_uscm": 620,
            "totalcoliform_mv_raw": 50.0,
            "totalcoliform_mv": 0.5
        },
        "badges": {
            "temp_c": {"status": "safe", "color": "green", "label": "Normal"},
            "do_mgl": {"status": "safe", "color": "green", "label": "Optimal"},
            "ph": {"status": "safe", "color": "green", "label": "Netral"},
            "conductivity_uscm": {"status": "safe", "color": "green", "label": "Normal"},
            "totalcoliform_mv": {"status": "safe", "color": "green", "label": "Aman"}
        },
        "sensor_ids": {
            "ph_temp": "PH_TEMP_SLAVE_ID",
            "do": "DO_SLAVE_ID",
            "conductivity": "EC_SLAVE_ID",
            "totalcoliform": "ECOLI_SLAVE_ID"
        },
        "total_records": 42
    }
    ```
    
    **Badge Status**:
    - `safe` (green): Parameter dalam batas aman
    - `warning` (yellow): Parameter di zona peringatan
    - `danger` (red): Parameter berbahaya
    
    **No Data Response**:
    ```json
    {
        "status": "no_data",
        "message": "No IoT data available yet",
        "data": null
    }
    ```
    
    **Status Codes**:
    - `200 OK`: Data tersedia (atau no_data)
    """
    if len(iot_data_storage) == 0:
        logger.warning("No IoT data available - storage is empty")
        return {
            "status": "no_data",
            "message": "No IoT data available yet",
            "data": None
        }
    
    latest = iot_data_storage[-1]
    
    logger.info(f"Fetching latest IoT data: timestamp={latest.get('timestamp')}")
    
    # Generate badges untuk semua parameter termasuk coliform sensor
    # Gunakan default thresholds
    th = Thresholds()
    
    # Buat dictionary untuk badge calculation (gunakan nilai MPN/100mL untuk coliform)
    readings_for_badge = {
        "temp_c": latest.get("temp_c"),
        "do_mgl": latest.get("do_mgl"),
        "ph": latest.get("ph"),
        "conductivity_uscm": latest.get("conductivity_uscm"),
        "totalcoliform_mv": latest.get("totalcoliform_mv")  # Gunakan nilai terkonversi (MPN/100mL)
    }
    
    badges = status_badges(readings_for_badge, th)
    
    return {
        "status": "success",
        "data": latest,
        "badges": badges,
        "sensor_ids": SENSOR_IDS,  # Include sensor IDs configuration
        "total_records": len(iot_data_storage)
    }

@app.get(
    "/iot/history",
    tags=["IoT Data Management"],
    summary="Dapatkan History Data IoT",
    response_description="Daftar data sensor historis"
)
def get_iot_history(limit: int = 50):
    """
    ## IoT History Data Endpoint
    
    Endpoint untuk mendapatkan data historis dari sensor IoT.
    
    **Use Case**:
    - Tabel riwayat data di dashboard
    - Analisis tren kualitas air
    - Export data untuk laporan
    
    **Query Parameters**:
    - `limit` (integer): Jumlah data terbaru (default: 50, max: 1000)
    
    **Response Example**:
    ```json
    {
        "status": "success",
        "data": [
            {
                "timestamp": "2025-11-07T14:30:00",
                "sensor_ids": {
                    "ph_temp": "PH_TEMP_SLAVE_ID",
                    "do": "DO_SLAVE_ID",
                    "conductivity": "EC_SLAVE_ID",
                    "totalcoliform": "ECOLI_SLAVE_ID"
                },
                "temp_c": 27.8,
                "do_mgl": 6.2,
                "ph": 7.2,
                "conductivity_uscm": 620,
                "totalcoliform_mv_raw": 50.0,
                "totalcoliform_mv": 0.5
            },
            {
                "timestamp": "2025-11-07T13:30:00",
                "sensor_ids": {
                    "ph_temp": "PH_TEMP_SLAVE_ID",
                    "do": "DO_SLAVE_ID",
                    "conductivity": "EC_SLAVE_ID",
                    "totalcoliform": "ECOLI_SLAVE_ID"
                },
                "temp_c": 28.1,
                "do_mgl": 6.0,
                "ph": 7.3,
                "conductivity_uscm": 615,
                "totalcoliform_mv_raw": 45.0,
                "totalcoliform_mv": 0.45
            }
        ],
        "sensor_ids": {
            "ph_temp": "PH_TEMP_SLAVE_ID",
            "do": "DO_SLAVE_ID",
            "conductivity": "EC_SLAVE_ID",
            "totalcoliform": "ECOLI_SLAVE_ID"
        },
        "count": 2,
        "total_records": 42
    }
    ```
    
    **Data Structure**:
    - Array data sensor diurutkan dari lama → baru
    - Timestamp dalam format ISO 8601
    - Total Coliform sudah terkonversi ke MPN/100mL
    
    **No Data Response**:
    ```json
    {
        "status": "no_data",
        "message": "No IoT data available yet",
        "data": []
    }
    ```
    
    **Example Request**:
    ```bash
    # Ambil 10 data terbaru
    curl "http://localhost:8000/iot/history?limit=10"
    
    # Ambil semua data (max 1000)
    curl "http://localhost:8000/iot/history?limit=1000"
    ```
    
    **Status Codes**:
    - `200 OK`: Data tersedia (atau no_data jika kosong)
    """
    logger.info(f"Fetching IoT history: limit={limit}, total_records={len(iot_data_storage)}")
    
    if len(iot_data_storage) == 0:
        logger.warning("No IoT history data available")
        return {
            "status": "no_data",
            "message": "No IoT data available yet",
            "data": []
        }
    
    # Ambil data terbaru sebanyak limit
    history = list(iot_data_storage)[-limit:]
    
    logger.info(f"✓ Returning {len(history)} history records")
    
    return {
        "status": "success",
        "data": history,
        "sensor_ids": SENSOR_IDS,  # Include sensor IDs configuration
        "count": len(history),
        "total_records": len(iot_data_storage)
    }

@app.post(
    "/iot/predict",
    tags=["IoT Data Management"],
    summary="Auto-Predict dari Data IoT Terbaru (Tanpa Input)",
    response_description="Hasil prediksi AI dari data sensor terbaru"
)
def predict_from_iot():
    """
    ## Auto-Prediction from Latest IoT Data (No Input Required)
    
    Endpoint untuk **OTOMATIS** melakukan prediksi AI dari data sensor IoT terbaru.
    **TIDAK PERLU KIRIM PARAMETER** - data diambil otomatis dari storage!
    
    ---
    
    ### 🔀 **Perbedaan `/predict` vs `/iot/predict`:**
    
    | Aspek | `/predict` | `/iot/predict` (Endpoint ini) |
    |-------|-----------|-------------------------------|
    | **Input** | ✅ Manual (kirim parameter) | ❌ Auto (ambil dari sensor) |
    | **Request Body** | ✅ Required | ❌ Empty (POST tanpa body!) |
    | **Use Case** | Testing, simulasi, lab validation | Real-time monitoring, automation |
    | **User** | Human (researcher, technician) | Machine (scheduler, automation) |
    
    ### ✅ **Kapan Pakai `/iot/predict` (Endpoint Ini):**
    - 🤖 **Automation/Cron Job**: Prediksi periodik tanpa input manual
    - 📊 **Real-time Dashboard**: Auto-refresh setiap X menit
    - 🔔 **Alert System**: Trigger notifikasi berdasarkan prediksi
    - 📡 **IoT Monitoring**: Setelah sensor kirim data via `/iot/data`
    - ⚡ **Quick Prediction**: Cepat! 1 API call tanpa perlu fetch data dulu
    
    ### ❌ **Jangan Pakai `/iot/predict` Jika:**
    - Belum ada data IoT di storage → Error 404 (gunakan `/predict` untuk manual input)
    - Mau test parameter custom → Pakai `/predict` (bisa input apa saja)
    - Data bukan dari sensor IoT → Pakai `/predict` (untuk lab test, simulasi, dll)
    
    ---
    
    ### 📋 **Workflow Typical**:
    ```
    Step 1: ESP32 kirim data sensor
    POST /iot/data
    {
      "temp_c": 27.8,
      "do_mgl": 6.2,
      "ph": 7.2,
      "conductivity_uscm": 620,
    }
    
    Step 2: API simpan data ke storage ✅
    
    Step 3: Trigger auto-predict (TANPA PARAMETER!)
    POST /iot/predict  ← Empty body!
    
    Step 4: Dapatkan hasil prediksi + metadata IoT ✅
    ```
    
    ---
    
    **Flow Internal**:
    1. Ambil data sensor terbaru dari `iot_data_storage`
    2. Convert ke format `PredictRequest`
    3. Jalankan AI prediction (sama seperti `/predict`)
    4. Return hasil + metadata IoT tambahan
    
    **Response Example**:
    ```json
    {
        "input_used": {...},
        "prediction": {
            "total_coliform_mpn_100ml": 0.45,
            "ci90_low": 0.20,
            "ci90_high": 0.85,
            "disclaimer": "Estimasi AI berbasis 4 parameter fisiko-kimia (bukan hasil uji lab)."
        },
        "ai_detection": {
            "potable": true,
            "severity": "safe",
            "reasons": [...],
            "recommendations": [...],
            "alternative_use": null,
            "thresholds": {...}
        },
        "status_badges": {...},
        "iot_timestamp": "2025-11-07T14:30:00",
        "iot_source": "mappi32"
    }
    ```
    
    **Metadata Tambahan**:
    - `iot_timestamp`: Waktu data sensor diterima
    - `iot_source`: Sumber data (mappi32/esp32)
    
    **Error Cases**:
    - **404 Not Found**: Belum ada data IoT tersimpan
    
    **Example Request**:
    ```bash
    curl -X POST "http://localhost:8000/iot/predict"
    ```
    
    **Status Codes**:
    - `200 OK`: Prediksi berhasil
    - `404 Not Found`: Belum ada data IoT
    - `500 Internal Server Error`: Error pada model AI
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
        totalcoliform_mv=None
    )
    
    # Gunakan endpoint predict yang sudah ada
    result = predict(req)
    
    # Tambahkan info IoT
    result["iot_timestamp"] = latest["timestamp"]
    result["iot_source"] = "mappi32"
    
    return result

@app.delete(
    "/iot/clear",
    tags=["IoT Data Management"],
    summary="Hapus Semua Data IoT",
    response_description="Konfirmasi penghapusan data"
)
def clear_iot_data():
    """
    ## Clear All IoT Data
    
    Endpoint untuk menghapus semua data IoT dari storage.
    
    **⚠️ PERINGATAN**: Endpoint ini akan menghapus SEMUA data historis!
    
    **Use Case**:
    - Testing dan development
    - Reset data setelah maintenance
    - Clear data sebelum deployment baru
    
    **Behavior**:
    - Menghapus semua data dari in-memory deque
    - Tidak dapat di-undo (permanent deletion)
    - Storage kembali ke state kosong
    
    **Response Example**:
    ```json
    {
        "status": "success",
        "message": "All IoT data cleared"
    }
    ```
    
    **Security Note**:
    - Di production, endpoint ini harus dilindungi dengan authentication
    - Pertimbangkan menambahkan confirmation token
    - Log semua clear operations untuk audit trail
    
    **Example Request**:
    ```bash
    curl -X DELETE "http://localhost:8000/iot/clear"
    ```
    
    **Status Codes**:
    - `200 OK`: Data berhasil dihapus
    """
    record_count = len(iot_data_storage)
    logger.warning(f"🗑️ CLEAR REQUEST: Deleting {record_count} IoT records from storage")
    
    iot_data_storage.clear()
    
    logger.warning(f"✓ All IoT data cleared successfully. {record_count} records deleted.")
    
    return {
        "status": "success",
        "message": "All IoT data cleared",
        "deleted_records": record_count
    }

# ====== PUBLIC API ENDPOINTS (GET) ======

@app.get(
    "/api/latest",
    tags=["Public API"],
    summary="Get Latest Water Quality Status (Simple GET)",
    response_description="Status kualitas air terbaru (sensor + AI prediction)"
)
def get_latest_status():
    """
    ## 🌐 Public API: Latest Water Quality Status
    
    **ENDPOINT PALING MUDAH** untuk website eksternal yang ingin menampilkan status kualitas air.
    
    ---
    
    ### ✅ **Kenapa Endpoint Ini Best Choice?**
    
    - 🚀 **Super Simple**: GET request tanpa parameter apapun
    - 📊 **Complete Data**: Sensor readings + AI prediction + Status badges
    - 🔄 **Always Fresh**: Data dari sensor IoT terbaru
    - 🎯 **Ready to Display**: Response sudah siap untuk ditampilkan langsung
    - 🌍 **CORS Enabled**: Bisa dipanggil dari domain manapun
    - 📱 **Mobile Friendly**: Lightweight response, cocok untuk mobile app
    
    ---
    
    ### 🎯 **Use Cases:**
    
    1. **Website/Blog Embed**
       - Tampilkan widget status kualitas air real-time
       - Refresh otomatis setiap X menit
    
    2. **Mobile App Integration**
       - Fetch data untuk ditampilkan di dashboard app
       - Tidak perlu handle POST request yang kompleks
    
    3. **IoT Display/Kiosk**
       - Layar monitor yang menampilkan status air
       - Polling periodik untuk update data
    
    4. **Third-Party Integration**
       - Website pemerintah/kampus yang butuh data kualitas air
       - News portal untuk laporan kualitas air
    
    ---
    
    ### 📊 **Response Structure:**
    
    ```json
    {
      "timestamp": "2025-11-21T14:30:00+07:00",
      "sensor_data": {
        "temp_c": 27.8,
        "do_mgl": 6.2,
        "ph": 7.2,
        "conductivity_uscm": 620,
        "totalcoliform_mv": 0.500
      },
      "prediction": {
        "total_coliform_mv": 0.450,
        "confidence_interval": {
          "low": 0.350,
          "high": 0.550
        }
      },
      "status": {
        "potable": true,
        "severity": "safe",
        "label": "LAYAK MINUM",
        "color": "green",
        "icon": "✅"
      },
      "badges": {
        "temp_c": {"status": "safe", "label": "Normal", "color": "green"},
        "do_mgl": {"status": "safe", "label": "Optimal", "color": "green"},
        "ph": {"status": "safe", "label": "Netral", "color": "green"},
        "conductivity_uscm": {"status": "safe", "label": "Normal", "color": "green"},
        "totalcoliform_mv": {"status": "safe", "label": "Aman", "color": "green"}
      }
    }
    ```
    
    ---
    
    ### 💡 **Quick Start Examples:**
    
    **JavaScript (Vanilla):**
    ```javascript
    fetch('https://gary29-water-quality-ai.hf.space/api/latest')
      .then(res => res.json())
      .then(data => {
        console.log('Status:', data.status.label);
        console.log('Severity:', data.status.severity);
      });
    ```
    
    **HTML (Direct Access):**
    ```html
    <script>
      async function checkWaterQuality() {
        const response = await fetch('YOUR_API_URL/api/latest');
        const data = await response.json();
        
        document.getElementById('status').innerHTML = 
          `<h2>${data.status.icon} ${data.status.label}</h2>
           <p>Suhu: ${data.sensor_data.temp_c}°C</p>
           <p>DO: ${data.sensor_data.do_mgl} mg/L</p>
           <p>pH: ${data.sensor_data.ph}</p>`;
      }
    </script>
    ```
    
    **PHP:**
    ```php
    $data = json_decode(file_get_contents('YOUR_API_URL/api/latest'), true);
    echo "Status: " . $data['status']['label'];
    ```
    
    **Python:**
    ```python
    import requests
    data = requests.get('YOUR_API_URL/api/latest').json()
    print(f"Status: {data['status']['label']}")
    ```
    
    ---
    
    ### ⚠️ **Error Responses:**
    
    **404 - No Data Available:**
    ```json
    {
      "detail": "Belum ada data IoT. Tunggu ESP32 mengirim data pertama."
    }
    ```
    
    **500 - Server Error:**
    ```json
    {
      "detail": "Error message details"
    }
    ```
    
    ---
    
    ### 📝 **Notes:**
    
    - Data diambil dari sensor IoT terbaru yang tersimpan
    - AI prediction menggunakan Random Forest model
    - Status severity: `safe` (hijau) / `warning` (kuning) / `danger` (merah)
    - Badge status untuk setiap parameter air
    - Timestamp dalam zona waktu WIB (UTC+7)
    
    ---
    
    **Status Codes:**
    - `200 OK`: Data berhasil diambil
    - `404 Not Found`: Belum ada data IoT
    - `500 Internal Server Error`: Error pada server
    """
    
    # Check if IoT data available
    if len(iot_data_storage) == 0:
        logger.warning("GET /api/latest - No IoT data available")
        raise HTTPException(
            status_code=404,
            detail="Belum ada data IoT. Tunggu ESP32 mengirim data pertama."
        )
    
    try:
        # Get latest IoT data
        latest = iot_data_storage[-1]
        
        logger.info(f"GET /api/latest - Fetching data from timestamp: {latest.get('timestamp')}")
        
        # Build predict request
        req = PredictRequest(
            temp_c=latest.get("temp_c", 0),
            do_mgl=latest.get("do_mgl", 0),
            ph=latest.get("ph", 0),
            conductivity_uscm=latest.get("conductivity_uscm", 0),
            totalcoliform_mv=latest.get("totalcoliform_mv", None)
        )
        
        # Use default thresholds
        th = Thresholds()
        
        # 1) Prediksi mikroba dari 4 fitur
        features = {
            "temp_c": float(req.temp_c),
            "do_mgl": float(req.do_mgl),
            "ph": float(req.ph),
            "conductivity_uscm": float(req.conductivity_uscm),
        }
        infer = rfw.predict_with_interval(features)

        # 2) Keputusan potabilitas
        readings = dict(features)
        if req.totalcoliform_mv is not None:
            readings["totalcoliform_mv"] = float(req.totalcoliform_mv)

        decision = decide_potability(readings, infer.pred_total_coliform_mv, th)

        # 3) Badge status per parameter
        readings_for_badge = dict(readings)
        badges = status_badges(readings_for_badge, th)
        
        # 4) Determine color and icon based on severity
        severity_map = {
            "safe": {"color": "green", "icon": "✅", "label": "LAYAK MINUM"},
            "warning": {"color": "yellow", "icon": "⚠️", "label": "PERLU PERHATIAN"},
            "danger": {"color": "red", "icon": "❌", "label": "TIDAK LAYAK MINUM"}
        }
        
        severity_info = severity_map.get(decision.severity, severity_map["safe"])
        
        logger.info(f"GET /api/latest - Status: {decision.severity} | Potable: {decision.potable} | Coliform: {infer.pred_total_coliform_mv:.3f}")
        
        # 5) Build response
        return {
            "timestamp": latest.get("timestamp"),
            "sensor_data": {
                "temp_c": latest.get("temp_c"),
                "do_mgl": latest.get("do_mgl"),
                "ph": latest.get("ph"),
                "conductivity_uscm": latest.get("conductivity_uscm"),
                "totalcoliform_mv_raw": latest.get("totalcoliform_mv_raw"),
                "totalcoliform_mv": latest.get("totalcoliform_mv")
            },
            "prediction": {
                "total_coliform_mv": infer.pred_total_coliform_mv,
                "confidence_interval": {
                    "low": infer.pred_ci90_low,
                    "high": infer.pred_ci90_high
                }
            },
            "status": {
                "potable": decision.potable,
                "severity": decision.severity,
                "label": severity_info["label"],
                "color": severity_info["color"],
                "icon": severity_info["icon"],
                "reasons": decision.reasons,
                "recommendations": decision.recommendations
            },
            "badges": badges
        }
        
    except Exception as e:
        logger.error(f"GET /api/latest - Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating status: {str(e)}")
