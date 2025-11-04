---
title: Water Quality AI API
emoji: 🌊
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
license: mit
---

# 🌊 Water Quality AI Monitoring System

Sistem pemantauan kualitas air berbasis AI menggunakan Random Forest untuk memprediksi Total Coliform dan menentukan kelayakan air minum.

## 🎯 Live Demo

**API Base URL**: `https://huggingface.co/spaces/YOUR_USERNAME/water-quality-ai`

### 📡 Endpoints

1. **POST /predict** - Prediksi Total Coliform dari sensor readings
2. **POST /iot/data** - Submit data dari IoT sensor (ESP32)
3. **GET /iot/latest** - Ambil data IoT terbaru
4. **GET /iot/history** - Ambil history data IoT
5. **DELETE /iot/clear** - Hapus semua history data
6. **GET /docs** - Interactive API documentation (Swagger UI)

## 🧪 Cara Menggunakan API

### Example: Predict Water Quality

```bash
curl -X POST "https://huggingface.co/spaces/YOUR_USERNAME/water-quality-ai/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "temp_c": 27.0,
    "do_mgl": 7.0,
    "ph": 7.5,
    "conductivity_uscm": 300.0
  }'
```

### Response:
```json
{
  "input_used": {
    "temp_c": 27.0,
    "do_mgl": 7.0,
    "ph": 7.5,
    "conductivity_uscm": 300.0
  },
  "prediction": {
    "total_coliform_mpn_100ml": 0.004,
    "ci90_low": 0.0,
    "ci90_high": 0.01,
    "disclaimer": "Estimasi AI berbasis 4 parameter fisiko-kimia (bukan hasil uji lab)."
  },
  "ai_detection": {
    "potable": true,
    "reasons": [],
    "recommendations": [],
    "alternative_use": ["Irigasi non-sensitif", "Perikanan", "Utility"],
    "thresholds": {
      "total_coliform_max_mpn_100ml": 0.7,
      "ph_min": 6.5,
      "ph_max": 8.5,
      "conductivity_max_uscm": 1500.0,
      "do_min_info_mgl": 5.0
    }
  },
  "status_badges": {
    "ph": ["optimal", "Optimal"],
    "do_mgl": ["good", "Aman (biologi)"],
    "conductivity_uscm": ["normal", "Normal"]
  }
}
```

## 📊 Model Information

- **Algorithm**: Random Forest Regressor
- **Input Features**: 
  - Temperature (°C)
  - Dissolved Oxygen (mg/L)
  - pH
  - Conductivity (µS/cm)
- **Output**: Total Coliform (MPN/100mL)
- **Model Version**: scikit-learn 1.7.2
- **Trained on**: Water quality dataset with log1p transformation

## 📈 Water Quality Thresholds

| Parameter | Safe Range | Unit | Notes |
|-----------|------------|------|-------|
| Total Coliform | ≤ 0.70 | MPN/100mL | Toleransi untuk fluktuasi parameter |
| pH | 6.5 - 8.5 | - | - |
| Conductivity | ≤ 1500 | µS/cm | Indikasi TDS |
| DO (info) | ≥ 5.0 | mg/L | Tidak memblok potabilitas |

## 🚀 Tech Stack

- **Backend**: FastAPI 0.114.2
- **ML Framework**: scikit-learn 1.7.2
- **Runtime**: Python 3.11
- **Server**: Uvicorn
- **Deployment**: Docker on Hugging Face Spaces

## 🔗 Integration with IoT

API ini support integrasi dengan ESP32/Arduino untuk real-time monitoring:

1. ESP32 kirim data sensor via POST `/iot/data`
2. Dashboard fetch data via GET `/iot/latest`
3. History tracking via GET `/iot/history`

## 📝 License

MIT License - Free to use for educational and commercial purposes.

## 👨‍💻 Developer

Developed with ❤️ for water quality monitoring applications.

---

**Note**: Ini adalah estimasi AI berdasarkan parameter fisiko-kimia, bukan hasil uji laboratorium resmi. Untuk keputusan krusial, lakukan verifikasi lab.
