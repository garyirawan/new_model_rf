# 🚀 PANDUAN DEPLOY KE CLOUD - STEP BY STEP

## Pilihan Platform Cloud (Gratis untuk Mulai)

1. **Render** ⭐ RECOMMENDED - Paling mudah
2. **Railway** - Bagus, tapi perlu kartu kredit
3. **Google Cloud Run** - Lebih advanced

---

## 📋 LANGKAH 1: PERSIAPAN (5 menit)

### 1.1 Pastikan semua file ada
✅ File-file ini sudah saya buatkan:
- `Procfile` - Instruksi untuk menjalankan server
- `runtime.txt` - Versi Python
- `.gitignore` - File yang diabaikan git
- `DEPLOYMENT.md` - Panduan deployment
- `README.md` - Dokumentasi project

### 1.2 Cek file model ada
```bash
dir rf_total_coliform_log1p_improved.joblib
```
Harus ada dan ukuran > 0 bytes

### 1.3 Test local dulu (pastikan jalan)
```bash
# Backend
uvicorn backend_fastapi:app --reload --port 8000

# Frontend
npm run dev
```

---

## 📋 LANGKAH 2: UPLOAD KE GITHUB (10 menit)

### 2.1 Inisialisasi Git (jika belum)
```bash
git init
git add .
git commit -m "Initial commit - Water Quality AI"
```

### 2.2 Push ke GitHub
```bash
# Buat repository baru di GitHub: github.com/new
# Nama: water-quality-ai (atau terserah)

git remote add origin https://github.com/garyirawan/water-quality-ai.git
git branch -M main
git push -u origin main
```

**⚠️ PENTING**: Pastikan file model `.joblib` ikut ter-upload!

---

## 📋 LANGKAH 3: DEPLOY BACKEND KE RENDER (15 menit)

### 3.1 Buat Akun Render
1. Buka: https://render.com
2. Klik **"Get Started"**
3. Sign up dengan **GitHub account** (recommended)
4. Authorize Render untuk akses repository

### 3.2 Create Web Service
1. Setelah login, klik **"New +"** (pojok kanan atas)
2. Pilih **"Web Service"**
3. Connect repository:
   - Pilih **"Connect a repository"**
   - Cari **"water-quality-ai"** (atau nama repo Anda)
   - Klik **"Connect"**

### 3.3 Configure Service
Isi form dengan:

| Field | Value |
|-------|-------|
| **Name** | `water-quality-ai` |
| **Region** | Singapore (atau terdekat) |
| **Branch** | `main` |
| **Root Directory** | (kosongkan) |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn backend_fastapi:app --host 0.0.0.0 --port $PORT` |
| **Plan** | `Free` |

### 3.4 Environment Variables (Optional)
Klik **"Advanced"** > **"Add Environment Variable"**:
```
MODEL_PATH=rf_total_coliform_log1p_improved.joblib
FEATURES_ORDER_PATH=model_features_order.txt
```

### 3.5 Deploy!
1. Klik **"Create Web Service"**
2. Tunggu build process (5-10 menit pertama kali)
3. Lihat logs untuk memastikan sukses

### 3.6 Dapatkan URL API
Setelah deploy sukses, Anda akan dapat URL seperti:
```
https://water-quality-ai.onrender.com
```

**SIMPAN URL INI!** Akan digunakan di frontend.

### 3.7 Test API
```bash
# Test health check
curl https://water-quality-ai.onrender.com/health

# Test predict
curl -X POST https://water-quality-ai.onrender.com/predict \
  -H "Content-Type: application/json" \
  -d "{\"temp_c\":27.8,\"do_mgl\":6.2,\"ph\":7.2,\"conductivity_uscm\":620}"
```

---

## 📋 LANGKAH 4: UPDATE FRONTEND (5 menit)

### 4.1 Update API URL
Edit file: `frontend_water_quality_dashboard_react.tsx`

Cari baris ini (sekitar line 17):
```typescript
const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
```

Ganti menjadi:
```typescript
const API_BASE = import.meta.env.VITE_API_BASE || "https://water-quality-ai.onrender.com";
```

### 4.2 Test Local dengan Cloud Backend
```bash
npm run dev
```

Buka http://localhost:3000 dan coba prediksi. Sekarang frontend local akan call API dari cloud!

---

## 📋 LANGKAH 5: DEPLOY FRONTEND (OPTIONAL) (15 menit)

### Opsi A: Deploy ke Vercel (Recommended untuk React)

#### 5.1 Install Vercel CLI
```bash
npm install -g vercel
```

#### 5.2 Deploy
```bash
vercel
```

Follow prompts:
- Project name: `water-quality-dashboard`
- Setup and deploy?: `Yes`

#### 5.3 Set Environment Variable
```bash
vercel env add VITE_API_BASE production
```
Masukkan: `https://water-quality-ai.onrender.com`

#### 5.4 Deploy Production
```bash
vercel --prod
```

Anda akan dapat URL seperti:
```
https://water-quality-dashboard.vercel.app
```

### Opsi B: Deploy ke Netlify

1. Buka: https://netlify.com
2. Drag & drop folder `dist/` hasil build
3. Atau connect GitHub repository

---

## 📋 LANGKAH 6: VERIFIKASI & TESTING (5 menit)

### 6.1 Test Backend di Cloud
```bash
curl https://water-quality-ai.onrender.com/health
# Expected: {"status":"ok"}
```

### 6.2 Test Full Flow
1. Buka frontend (local atau cloud)
2. Input parameter:
   - Suhu: 27.8
   - DO: 6.2
   - pH: 7.2
   - Konduktivitas: 620
3. Klik "Prediksi & Evaluasi"
4. Harus muncul hasil prediksi

### 6.3 Cek Browser Console
- Tidak ada error CORS
- Request sukses (status 200)
- Data received dari cloud

---

## 🎉 SELESAI!

Sistem Anda sekarang sudah di cloud:

✅ **Backend API**: `https://water-quality-ai.onrender.com`
✅ **Model AI**: Running di cloud server
✅ **Database**: Tidak perlu (stateless API)
✅ **Frontend**: Bisa akses dari mana saja

---

## 🔧 TROUBLESHOOTING

### Error: Build Failed
- Check logs di Render dashboard
- Pastikan `requirements.txt` lengkap
- Pastikan Python version compatible

### Error: Model not found
- Pastikan file `.joblib` ada di repository
- Check file size (tidak 0 bytes)
- Verify path di environment variables

### Error: 500 Internal Server Error
- Check Render logs
- Mungkin model corrupted saat upload
- Try re-deploy

### Frontend tidak bisa connect
- Check CORS settings di backend
- Pastikan URL API benar (https, bukan http)
- Check browser console untuk error

### Cold Start Lambat
- Normal untuk free tier Render
- First request bisa 10-30 detik
- Subsequent requests cepat

---

## 💡 TIPS

1. **Free Tier Limits**:
   - Render: 750 hours/month gratis
   - Server sleep setelah 15 menit idle
   - First request akan lambat (cold start)

2. **Keep Alive**:
   - Buat cron job ping `/health` tiap 10 menit
   - Gunakan UptimeRobot (gratis)

3. **Monitoring**:
   - Check Render dashboard untuk logs
   - Monitor response time
   - Set up alerts

4. **Updates**:
   - Push ke GitHub
   - Render auto-deploy (jika enabled)
   - Atau manual deploy di dashboard

---

## 📞 BUTUH BANTUAN?

Jika ada error, cek:
1. Render logs
2. Browser console
3. Network tab (DevTools)

Atau tanya saya! 😊
