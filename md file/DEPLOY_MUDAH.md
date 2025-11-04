# 🇮🇩 CARA DEPLOY KE CLOUD - RINGKAS & MUDAH

## 🎯 Tujuan
Upload model AI ke cloud server agar bisa diakses dari mana saja tanpa perlu jalankan backend di komputer lokal.

---

## 📝 PERSIAPAN (SUDAH SAYA SIAPKAN)

Saya sudah membuatkan file-file ini untuk Anda:

✅ `Procfile` - Cara menjalankan server di cloud
✅ `runtime.txt` - Versi Python
✅ `.gitignore` - File yang tidak perlu di-upload
✅ `requirements.txt` - Library Python yang dibutuhkan
✅ `DEPLOYMENT_STEP_BY_STEP.md` - Panduan lengkap (bahasa Inggris)
✅ `deploy.ps1` - Script otomatis untuk Windows
✅ `README.md` - Dokumentasi project

---

## 🚀 LANGKAH SINGKAT (30 MENIT)

### 1️⃣ UPLOAD KE GITHUB (10 menit)

**Cara Mudah - Gunakan Script Otomatis:**
```powershell
.\deploy.ps1
```

Script akan tanya:
- Commit message: (tekan Enter saja)
- URL GitHub: masukkan link repository Anda

**Cara Manual:**
```bash
git init
git add .
git commit -m "Deploy to cloud"
git remote add origin https://github.com/USERNAME/REPO-NAME.git
git push -u origin main
```

---

### 2️⃣ DEPLOY DI RENDER (15 menit)

**a. Buat Akun (2 menit)**
1. Buka: https://render.com
2. Klik "Get Started"
3. Login dengan **GitHub** (lebih mudah!)

**b. Buat Web Service (5 menit)**
1. Klik tombol **"New +"** (pojok kanan atas)
2. Pilih **"Web Service"**
3. Pilih repository yang tadi di-upload

**c. Setting (5 menit)**

Isi form:

| Kolom | Isi dengan |
|-------|------------|
| Name | `water-quality-ai` |
| Region | Singapore |
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn backend_fastapi:app --host 0.0.0.0 --port $PORT` |
| Instance Type | Free |

**d. Deploy!**
1. Klik **"Create Web Service"**
2. Tunggu 5-10 menit (build pertama kali)
3. Lihat status: harus jadi hijau ✅

**e. Simpan URL API**

Setelah selesai, Anda dapat URL seperti:
```
https://water-quality-ai.onrender.com
```

**⚠️ PENTING: SIMPAN URL INI!**

---

### 3️⃣ UPDATE FRONTEND (5 menit)

**a. Buka file:**
`frontend_water_quality_dashboard_react.tsx`

**b. Cari baris ini** (sekitar line 17):
```typescript
const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
```

**c. Ganti dengan URL cloud Anda:**
```typescript
const API_BASE = import.meta.env.VITE_API_BASE || "https://water-quality-ai.onrender.com";
```

**d. Save dan test:**
```bash
npm run dev
```

Buka http://localhost:3000 dan coba prediksi.
Sekarang frontend call API dari cloud! 🎉

---

## ✅ SELESAI!

Model AI Anda sekarang di cloud:

🌐 **URL API Cloud**: `https://water-quality-ai.onrender.com`

📱 **Bisa diakses dari**:
- Komputer mana saja
- Handphone
- Tablet
- Di mana saja ada internet

💰 **Biaya**: GRATIS (750 jam/bulan)

---

## 🧪 TEST CLOUD API

### Via Browser:
```
https://water-quality-ai.onrender.com/health
```

### Via PowerShell:
```powershell
Invoke-RestMethod -Uri "https://water-quality-ai.onrender.com/health"
```

### Test Prediksi:
```powershell
$body = @{
    temp_c = 27.8
    do_mgl = 6.2
    ph = 7.2
    conductivity_uscm = 620
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://water-quality-ai.onrender.com/predict" -Method POST -Body $body -ContentType "application/json"
```

---

## ⚠️ CATATAN PENTING

### 1. Cold Start (Normal)
- Server sleep setelah 15 menit tidak dipakai
- Request pertama akan lambat (10-30 detik)
- Request berikutnya cepat

### 2. Free Tier Limits
- 750 jam/bulan (cukup untuk 1 bulan penuh!)
- Server otomatis sleep jika idle
- No credit card needed

### 3. Update Model
Jika mau update model baru:
```bash
git add rf_total_coliform_log1p_improved.joblib
git commit -m "Update model"
git push
```
Render akan auto-deploy ulang!

---

## 🆘 TROUBLESHOOTING

### ❌ Build Failed
Cek logs di Render dashboard → klik "Logs"

### ❌ Model Not Found
Pastikan file `.joblib` ada di GitHub (ukuran > 0 bytes)

### ❌ Frontend ga bisa connect
- Pastikan URL di frontend benar
- Cek ada `https://` (bukan `http://`)
- Buka DevTools → Console untuk lihat error

### ❌ Response lambat
- Normal untuk cold start (request pertama)
- Wait 30 detik, coba lagi

---

## 💡 TIPS PRO

### Keep Server Alive (Optional)
Biar server tidak sleep, ping tiap 10 menit:
1. Buka: https://uptimerobot.com
2. Buat akun gratis
3. Add monitor → HTTP(s)
4. URL: `https://water-quality-ai.onrender.com/health`
5. Interval: 10 minutes

### Deploy Frontend ke Vercel (Optional)
Biar frontend juga di cloud:
```bash
npm install -g vercel
vercel
```

---

## 🎓 LANGKAH SELANJUTNYA

Setelah deploy sukses, Anda bisa:

1. ✅ Share URL ke teman/dosen
2. ✅ Akses dari HP
3. ✅ Presentasi tanpa setup lokal
4. ✅ Portfolio project online

---

## 📞 BUTUH BANTUAN?

Kalau ada error atau bingung:

1. Screenshot error message
2. Cek file `DEPLOYMENT_STEP_BY_STEP.md` (panduan lengkap)
3. Atau tanya saya! 😊

---

**Happy Deploying! 🚀**
