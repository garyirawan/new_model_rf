# 🚀 Checklist Deploy ke Hugging Face Spaces

## ✅ File yang Sudah Siap

### 1. **requirements.txt** ✅
```
fastapi==0.114.2       ← Match dengan environment VSCode
uvicorn[standard]==0.30.6
pydantic==2.8.2
scikit-learn==1.7.2    ← Match dengan environment VSCode
numpy==2.3.4           ← Match dengan environment VSCode
joblib==1.5.2          ← Match dengan environment VSCode
python-multipart==0.0.20
```

### 2. **Dockerfile** ✅
- Base image: `python:3.11-slim`
- Port: `7860` (Hugging Face default)
- Health check: Sudah ditambahkan
- Environment variables: Sudah diset
- Optimized layer caching
- Copy only necessary files

### 3. **.dockerignore** ✅
- Exclude frontend files (React/Vite)
- Exclude test files
- Exclude .git, .env
- Exclude deployment scripts
- Exclude Arduino/ESP32 files
- **INCLUDE**: backend_fastapi.py, inference_rf.py, model files

### 4. **README_HF.md** ✅
- Markdown header dengan metadata Hugging Face
- API documentation
- Example usage
- Model information
- Thresholds table

### 5. **Backend Files** ✅
- `backend_fastapi.py` - Main API ✅
- `inference_rf.py` - ML inference logic ✅
- `rf_total_coliform_log1p_improved.joblib` - Model file ✅
- `model_features_order.txt` - Feature order ✅

---

## 📦 File yang Akan Di-Push ke Hugging Face

```
water-quality-ai/  (Hugging Face Space)
├── Dockerfile                                    ← Deploy configuration
├── README.md                                     ← Rename README_HF.md → README.md
├── requirements.txt                              ← Python dependencies
├── backend_fastapi.py                            ← Main API
├── inference_rf.py                               ← ML logic
├── rf_total_coliform_log1p_improved.joblib      ← Model (100MB+)
└── model_features_order.txt                      ← Feature order
```

**TIDAK PERLU:**
- ❌ app.py (Dockerfile langsung run backend_fastapi.py)
- ❌ Frontend files (React/TypeScript)
- ❌ Test files
- ❌ ESP32 Arduino files
- ❌ Deploy scripts (deploy.sh, deploy.ps1)

---

## 🚀 Langkah Deploy

### Step 1: Persiapan File ✅ DONE
- [x] Update requirements.txt dengan versi yang match
- [x] Optimize Dockerfile
- [x] Update .dockerignore
- [x] Buat README_HF.md

### Step 2: Buat Space di Hugging Face ✅ DONE (by User)
- [x] Space name: `water-quality-ai`
- [x] SDK: Docker
- [x] Hardware: CPU basic (FREE)
- [x] Visibility: Public/Private

### Step 3: Clone Space ke Local
```bash
# Install git-lfs (jika belum)
git lfs install

# Clone Hugging Face Space
git clone https://huggingface.co/spaces/YOUR_USERNAME/water-quality-ai
cd water-quality-ai
```

### Step 4: Copy File yang Diperlukan
```bash
# From your project folder, copy these files:
cp backend_fastapi.py water-quality-ai/
cp inference_rf.py water-quality-ai/
cp rf_total_coliform_log1p_improved.joblib water-quality-ai/
cp model_features_order.txt water-quality-ai/
cp Dockerfile water-quality-ai/
cp requirements.txt water-quality-ai/

# Rename README for Hugging Face
cp README_HF.md water-quality-ai/README.md
```

### Step 5: Push ke Hugging Face
```bash
cd water-quality-ai

# Add all files
git add .

# Commit
git commit -m "Initial deploy: Water Quality AI API with Random Forest model"

# Push ke Hugging Face (akan trigger auto-build)
git push origin main
```

### Step 6: Tunggu Build (5-10 menit)
- Hugging Face akan build Docker image
- Install dependencies dari requirements.txt
- Start uvicorn server di port 7860
- Status bisa dicek di tab "Logs"

### Step 7: Test API
```bash
# Test endpoint
curl https://huggingface.co/spaces/YOUR_USERNAME/water-quality-ai/docs

# Test prediction
curl -X POST "https://YOUR_USERNAME-water-quality-ai.hf.space/predict" \
  -H "Content-Type: application/json" \
  -d '{"temp_c": 27, "do_mgl": 7, "ph": 7.5, "conductivity_uscm": 300}'
```

---

## ⚠️ Troubleshooting

### Build Failed?
- **Check Logs**: Tab "Logs" di Hugging Face Space
- **Common issues**:
  - Missing dependencies → Update requirements.txt
  - Large model file → Use git-lfs
  - Port conflict → Pastikan Dockerfile expose 7860

### Model File Too Large?
```bash
# Track model file dengan git-lfs
git lfs track "*.joblib"
git add .gitattributes
git add rf_total_coliform_log1p_improved.joblib
git commit -m "Track model with git-lfs"
git push
```

### API Timeout?
- Upgrade Space hardware (CPU basic → CPU boost)
- Optimize model loading
- Add caching

---

## 🔄 Update Frontend untuk Connect ke HF

Setelah backend deploy, update frontend:

```typescript
// frontend_water_quality_dashboard_react.tsx
const API_BASE = import.meta.env.VITE_API_BASE || 
  "https://YOUR_USERNAME-water-quality-ai.hf.space";
```

---

## 📊 Estimasi Biaya

- **CPU basic (FREE)**: 
  - ✅ 2 CPU cores
  - ✅ 16GB RAM
  - ✅ Unlimited usage untuk public spaces
  - ⚠️ Auto-sleep setelah 48 jam idle (akan wake saat request)

- **CPU boost ($0.50/hr)**:
  - Jika perlu always-on
  - Lebih cepat inference

---

## ✅ Ready to Deploy!

Semua file sudah siap. Tinggal ikuti Step 3-7 di atas! 🚀
