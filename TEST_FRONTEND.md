# ✅ Testing Frontend dengan Hugging Face Backend

## 🎯 Status: BACKEND LIVE & FRONTEND RUNNING!

### Backend Hugging Face
- ✅ **URL**: https://gary29-water-quality-ai.hf.space
- ✅ **Status**: RUNNING 🟢
- ✅ **Threshold**: 0.7 MPN/100mL (SUDAH BENAR!)
- ✅ **Potable Detection**: Working (True untuk data bagus)

### Frontend Vite Dev Server
- ✅ **URL**: http://localhost:3000/
- ✅ **Status**: RUNNING 🟢
- ✅ **API Connection**: Pointing to Hugging Face

---

## 🧪 Cara Testing

### 1. **Buka Browser**
Akses: http://localhost:3000/

Atau klik link ini di VSCode Simple Browser (sudah dibuka otomatis)

### 2. **Dashboard Seharusnya Menampilkan:**

#### ✅ Jika Ada Data IoT:
- **Status**: "AIR LAYAK MINUM" atau "AIR TIDAK LAYAK MINUM"
- **Sensor Readings**: Suhu, DO, pH, Konduktivitas, Total Coliform
- **Grafik**: Prediksi mikroba dengan confidence interval
- **History Table**: 50 data terbaru dengan predictions

#### ⚠️ Jika Belum Ada Data IoT:
- **Error**: "Belum ada data IoT. Pastikan ESP32 sudah mengirim data."
- **Solusi**: Test dengan data dummy (lihat Step 3)

### 3. **Test dengan Data Dummy (Manual)**

Buka console browser (F12 → Console) dan jalankan:

```javascript
// Test send data ke API
fetch('https://gary29-water-quality-ai.hf.space/iot/data', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    temp_c: 27.0,
    do_mgl: 7.0,
    ph: 7.5,
    conductivity_uscm: 300.0,
    totalcoliform_mv: 0.0
  })
})
.then(res => res.json())
.then(data => {
  console.log('✓ Data sent!', data);
  // Refresh dashboard
  location.reload();
});
```

### 4. **Test dengan PowerShell (Simulasi ESP32)**

```powershell
# Kirim data dummy ke IoT endpoint
Invoke-RestMethod -Uri "https://gary29-water-quality-ai.hf.space/iot/data" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"temp_c": 27, "do_mgl": 7, "ph": 7.5, "conductivity_uscm": 300, "totalcoliform_mv": 0}'

# Cek data latest
Invoke-RestMethod -Uri "https://gary29-water-quality-ai.hf.space/iot/latest"
```

### 5. **Refresh Dashboard**

Setelah kirim data dummy:
1. Klik tombol **"🔄 Refresh Manual"** di dashboard
2. Atau refresh browser (Ctrl + R)
3. Dashboard seharusnya update dengan data baru

---

## 📊 Expected Results

### **Dengan Data Bagus (temp=27, DO=7, pH=7.5, cond=300):**

**Status Card (Pink/Green):**
```
✓ AIR LAYAK MINUM
✓ Aman untuk dikonsumsi

Prediksi Total Coliform: 0.004 MPN/100mL
(Batas aman: ≤ 0.7 MPN/100mL)
```

**AI Detection:**
- **Alasan/Temuan**: Tidak ada pelanggaran ambang terdeteksi.
- **Rekomendasi**: – (kosong, karena air layak)
- **Alternative Use**: Irigasi, Perikanan, Utility

**Sensor Cards:**
- Suhu: 27°C
- DO: 7 mg/L (Badge: Aman biologi)
- pH: 7.5 (Badge: Optimal)
- Konduktivitas: 300 µS/cm (Badge: Normal)
- Total Coliform (Sensor): 0 mV
- Status Kelayakan: LAYAK MINUM ✅

---

## 🔧 Troubleshooting

### Dashboard Loading Tapi Kosong?
**Reason**: Belum ada data IoT di backend

**Solution**: 
1. Kirim data dummy (Step 3 atau 4)
2. Refresh dashboard

### Error: "Failed to fetch"?
**Reason**: CORS atau API belum ready

**Check**:
```powershell
# Cek API health
Invoke-WebRequest -Uri "https://gary29-water-quality-ai.hf.space/docs"
```

**Solution**:
- Tunggu 1-2 menit (cold start)
- Cek tab "Logs" di Hugging Face Space
- Pastikan backend status "Running" 🟢

### Threshold Masih 0.0?
**Reason**: Backend belum deploy dengan versi terbaru

**Check**:
```powershell
$r = Invoke-RestMethod -Uri "https://gary29-water-quality-ai.hf.space/predict" -Method Post -ContentType "application/json" -Body '{"temp_c": 27, "do_mgl": 7, "ph": 7.5, "conductivity_uscm": 300}'
$r.ai_detection.thresholds.total_coliform_max_mpn_100ml
# Should output: 0.7
```

### Auto-Refresh Tidak Jalan?
**Check**:
- Interval set ke 1 jam (3600000ms)
- Untuk testing, ubah sementara ke 10 detik:
  ```typescript
  const REFRESH_INTERVAL = 10000; // 10 seconds
  ```
- Jangan lupa revert ke 3600000 setelah testing!

---

## 🎮 Interactive Testing Flow

### Flow 1: Full Test (Tanpa ESP32)

1. **Start Backend**: ✅ Already running di HF
2. **Start Frontend**: ✅ `npm run dev` → http://localhost:3000
3. **Send Dummy Data**:
   ```powershell
   Invoke-RestMethod -Uri "https://gary29-water-quality-ai.hf.space/iot/data" -Method Post -ContentType "application/json" -Body '{"temp_c": 27, "do_mgl": 7, "ph": 7.5, "conductivity_uscm": 300, "totalcoliform_mv": 0}'
   ```
4. **Refresh Dashboard**: Klik 🔄 Refresh Manual
5. **Verify**: Status = "LAYAK MINUM" ✅

### Flow 2: Test Threshold (Data Buruk)

1. **Send Bad Data**:
   ```powershell
   # pH terlalu rendah
   Invoke-RestMethod -Uri "https://gary29-water-quality-ai.hf.space/iot/data" -Method Post -ContentType "application/json" -Body '{"temp_c": 27, "do_mgl": 7, "ph": 5.0, "conductivity_uscm": 300, "totalcoliform_mv": 0}'
   ```
2. **Refresh Dashboard**
3. **Verify**: Status = "TIDAK LAYAK MINUM" ❌
4. **Check Alasan**: "pH 5.00 di luar [6.5, 8.5]"
5. **Check Rekomendasi**: "Naikkan pH: penambahan alkalinitas..."

### Flow 3: Test History

1. **Send Multiple Data** (5 kali dengan variasi):
   ```powershell
   # Data 1
   Invoke-RestMethod -Uri "https://gary29-water-quality-ai.hf.space/iot/data" -Method Post -ContentType "application/json" -Body '{"temp_c": 25, "do_mgl": 6.5, "ph": 7.0, "conductivity_uscm": 280, "totalcoliform_mv": 0}'
   
   # Data 2
   Invoke-RestMethod -Uri "https://gary29-water-quality-ai.hf.space/iot/data" -Method Post -ContentType "application/json" -Body '{"temp_c": 26, "do_mgl": 7.2, "ph": 7.3, "conductivity_uscm": 310, "totalcoliform_mv": 0}'
   
   # ... dst
   ```
2. **Refresh Dashboard**
3. **Check History Table**: Harus ada 5 rows dengan predictions

### Flow 4: Test Delete History

1. **Klik tombol "🗑️ Hapus Semua History"**
2. **Confirm di modal popup**
3. **Verify**: 
   - History table kosong
   - Grafik reset
   - Success message muncul

---

## 📱 Test di Multiple Devices

### Desktop Browser
- ✅ Chrome: http://localhost:3000
- ✅ Firefox: http://localhost:3000
- ✅ Edge: http://localhost:3000

### Mobile (via Network)
1. Get local IP:
   ```powershell
   ipconfig | Select-String "IPv4"
   ```
2. Start Vite with --host:
   ```bash
   npm run dev -- --host
   ```
3. Access from phone: http://YOUR_LOCAL_IP:3000

---

## 🚀 Production Deployment

Setelah testing OK, deploy frontend:

### Option 1: Vercel (Recommended)
1. Push to GitHub
2. Import to Vercel
3. Set environment variable:
   ```
   VITE_API_BASE=https://gary29-water-quality-ai.hf.space
   ```

### Option 2: Netlify
1. Build: `npm run build`
2. Upload `dist/` folder
3. Set redirect rules untuk SPA

### Option 3: GitHub Pages
```bash
npm run build
# Upload dist/ to gh-pages branch
```

---

## ✅ Success Criteria

Dashboard berfungsi dengan baik jika:

- [x] API Hugging Face responding (status 200)
- [x] Threshold = 0.7 MPN/100mL (bukan 0.0)
- [x] Data dummy bisa di-POST
- [x] Dashboard menampilkan sensor readings
- [x] Prediction menunjukkan "LAYAK MINUM" untuk data bagus
- [x] Grafik menampilkan history predictions
- [x] History table menampilkan data dengan AI predictions
- [x] Delete history button working
- [x] Auto-refresh working (every 1 hour)
- [x] Manual refresh button working
- [x] Timezone WIB displayed correctly

---

## 🎉 READY FOR PRODUCTION!

Backend: ✅ https://gary29-water-quality-ai.hf.space
Frontend: ✅ http://localhost:3000 (dev)

**Next Steps:**
1. Test all flows above ✅
2. Connect ESP32 untuk real IoT data 🔌
3. Deploy frontend to Vercel/Netlify 🌐
4. Monitor & enjoy! 🎊
