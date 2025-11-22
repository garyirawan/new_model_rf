# 🌊 Water Quality AI Monitoring System

Sistem pemantauan kualitas air berbasis AI menggunakan Random Forest untuk memprediksi Total Coliform dan menentukan kelayakan air minum.

## 🚀 Features

- ✅ Prediksi Total Coliform (MPN/100mL) dari 4 parameter fisiko-kimia
- ✅ AI Detection untuk status kelayakan air minum
- ✅ Confidence Interval 90% untuk prediksi
- ✅ Real-time monitoring dengan visualisasi interaktif
- ✅ Rekomendasi tindakan otomatis
- ✅ Dashboard modern dengan React + Vite
- ✅ **Handling sensor rusak dengan nilai -1** (badge abu-abu)
- ✅ **GET API endpoint** untuk integrasi third-party website
- ✅ **Priority logic max-based**: ambil nilai tertinggi antara sensor dan AI prediction

## 📊 Model AI

- **Algorithm**: Random Forest Regressor
- **Input Features**: Suhu, DO, pH, Konduktivitas
- **Output**: Total Coliform (MPN/100mL)
- **Trained with**: scikit-learn 1.7.2
- **Model File**: `rf_total_coliform_log1p_improved.joblib`

## 🛠️ Tech Stack

### Backend
- FastAPI
- Python 3.11
- scikit-learn
- NumPy
- Uvicorn

### Frontend
- React 18
- TypeScript
- Vite
- Recharts (visualization)
- Tailwind CSS

## 🏃 Quick Start (Local)

### Backend
```bash
cd new_model_rf
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn backend_fastapi:app --reload --port 8000
```

### Frontend
```bash
npm install
npm run dev
```

Visit: http://localhost:3000

## ☁️ Cloud Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

### Quick Deploy to Render
1. Push to GitHub
2. Connect repository to Render
3. Deploy automatically
4. Get your API URL
5. Update frontend `API_BASE` URL

## 📝 API Endpoints

### Health Check
```bash
GET /health
```

### Predict Water Quality
```bash
POST /predict
Content-Type: application/json

{
  "temp_c": 27.8,
  "do_mgl": 6.2,
  "ph": 7.2,
  "conductivity_uscm": 620,
  "totalcoliform_mv": null  // optional (MPN/100mL)
}
```

**Response:**
```json
{
  "prediction": {
    "total_coliform_mv": 12.5,
    "ci90_low": 8.2,
    "ci90_high": 16.8
  },
  "ai_detection": {
    "potable": false,
    "reasons": ["Total Coliform terdeteksi: 12.5 MPN/100mL"],
    "recommendations": ["Lakukan disinfeksi (klorinasi/UV)"],
    "alternative_use": ["Irigasi pertanian", "Industri"]
  },
  "status_badges": {
    "ph": ["optimal", "Optimal"],
    "do_mgl": ["good", "Good"],
    "conductivity_uscm": ["normal", "Acceptable"]
  }
}
```

## 📈 Water Quality Thresholds

| Parameter | Safe Range | Unit | Notes |
|-----------|------------|------|-------|
| Total Coliform | ≤ 0.70 | MPN/100mL | Toleransi untuk fluktuasi parameter |
| pH | 6.5 - 8.5 | - | - |
| Conductivity | ≤ 1500 | µS/cm | Indikasi TDS |
| DO (info) | ≥ 5.0 | mg/L | Tidak memblok potabilitas |

> **Update Nov 2025**: Threshold Total Coliform diubah dari 0.0 ke 0.70 MPN/100mL untuk memberikan spare margin terhadap fluktuasi keempat parameter input (temperature, DO, pH, conductivity).

### 🔧 Sensor Rusak (Faulty Sensor)
**Konvensi:** ESP32 mengirim **nilai -1** untuk menandakan sensor rusak.

| Status | Badge Color | Behavior |
|--------|-------------|----------|
| **Faulty (-1)** | 🔘 Abu-abu | Sensor diabaikan, gunakan AI prediction saja |
| Unknown (None) | ⚪ Abu muda | Data tidak ada |

Lihat [SENSOR_RUSAK_HANDLING.md](docs/SENSOR_RUSAK_HANDLING.md) untuk detail implementasi.

### 📊 Priority Logic (Updated Nov 22, 2025)
**Max-based priority:** Ambil nilai **TERTINGGI** antara sensor dan AI prediction untuk keputusan kelayakan.

```
final_coliform = max(sensor_coliform, ai_prediction)
```

**Alasan:** Lebih konservatif untuk keamanan - prioritaskan nilai kontaminasi yang lebih tinggi.

## 🔧 Environment Variables

```bash
MODEL_PATH=rf_total_coliform_log1p_improved.joblib
FEATURES_ORDER_PATH=model_features_order.txt
VITE_API_BASE=http://localhost:8000  # Frontend
```

## 📦 Project Structure

```
new_model_rf/
├── backend_fastapi.py          # FastAPI backend
├── inference_rf.py             # Model inference logic
├── rf_total_coliform_log1p_improved.joblib  # Trained model
├── model_features_order.txt    # Feature order
├── frontend_water_quality_dashboard_react.tsx  # React dashboard
├── requirements.txt            # Python dependencies
├── package.json                # Node dependencies
├── docs/
│   ├── API_GET_ENDPOINT.md     # GET API documentation (6 languages)
│   ├── SENSOR_RUSAK_HANDLING.md # Sensor rusak (-1) handling guide
│   ├── FRONTEND_UPDATE_GET_API.md # Frontend integration notes
│   └── LOGGING_GUIDE.md        # Logging implementation
├── test_priority.py            # Test priority logic max-based
├── test_sensor_rusak.py        # Test sensor rusak handling
├── test_api_sensor_rusak.ps1   # API test untuk sensor rusak
└── water-quality-ai/           # Hugging Face deployment folder
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License

## 👤 Author

Gary Irawan

## 🙏 Acknowledgments

- Dataset: Water quality monitoring data
- Framework: FastAPI, React, scikit-learn
- Visualization: Recharts
