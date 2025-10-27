# Water Quality AI - Cloud Deployment Guide

## Deploy ke Render (Recommended - Gratis & Mudah)

### Step 1: Push ke GitHub
```bash
git add .
git commit -m "Prepare for cloud deployment"
git push origin main
```

### Step 2: Deploy di Render
1. Buka https://render.com
2. Sign up dengan GitHub account
3. Click "New +" → "Web Service"
4. Connect repository: `garyirawan/new_model_rf`
5. Configure:
   - **Name**: water-quality-ai
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend_fastapi:app --host 0.0.0.0 --port $PORT`
6. Click "Create Web Service"
7. Tunggu ~5-10 menit untuk build selesai

### Step 3: Dapatkan URL API
Setelah deploy selesai, Anda akan dapat URL seperti:
```
https://water-quality-ai.onrender.com
```

### Step 4: Update Frontend
Edit file `.env` atau langsung di `frontend_water_quality_dashboard_react.tsx`:
```typescript
const API_BASE = "https://water-quality-ai.onrender.com";
```

---

## Alternative: Deploy ke Railway

### Step 1: Push ke GitHub (sama seperti di atas)

### Step 2: Deploy di Railway
1. Buka https://railway.app
2. Sign up dengan GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Pilih repository `new_model_rf`
5. Railway akan auto-detect Python dan deploy
6. Tambahkan environment variable jika perlu

### Step 3: Dapatkan URL
Railway akan generate URL seperti:
```
https://new-model-rf-production.up.railway.app
```

---

## Alternative: Google Cloud Run (Lebih Advanced)

### Prerequisites:
- Google Cloud account
- gcloud CLI installed

### Step 1: Create Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "backend_fastapi:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Step 2: Deploy
```bash
gcloud run deploy water-quality-ai \
  --source . \
  --platform managed \
  --region asia-southeast1 \
  --allow-unauthenticated
```

---

## Verifikasi Deployment

Test API endpoint:
```bash
curl https://YOUR-CLOUD-URL/health
# Expected: {"status":"ok"}

curl -X POST https://YOUR-CLOUD-URL/predict \
  -H "Content-Type: application/json" \
  -d '{
    "temp_c": 27.8,
    "do_mgl": 6.2,
    "ph": 7.2,
    "conductivity_uscm": 620
  }'
```

---

## Important Notes

1. **Model File Size**: File `.joblib` akan di-upload ke cloud
2. **Cold Start**: First request mungkin lambat (5-10 detik)
3. **Free Tier Limits**: 
   - Render: 750 hours/month gratis
   - Railway: $5 credit/month gratis
4. **Environment Variables**: Set `MODEL_PATH` jika perlu custom path

---

## Troubleshooting

### Error: Model file not found
- Pastikan file `.joblib` ada di repository
- Check path di `backend_fastapi.py`

### Error: Out of memory
- Model terlalu besar untuk free tier
- Upgrade ke paid plan atau gunakan smaller model

### CORS Error
- Sudah handled di `backend_fastapi.py` dengan `allow_origins=["*"]`
- Untuk production, ganti dengan domain frontend yang spesifik
