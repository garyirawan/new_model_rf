# 🌐 Mode Monitoring IoT Real-Time

## 📖 Overview

Dashboard telah diubah dari **mode input manual** menjadi **mode monitoring IoT real-time**. Frontend sekarang secara otomatis mengambil data sensor terbaru dari backend tanpa memerlukan input manual.

## ✨ Fitur Baru

### 1. **Auto-Refresh Data**
- ✅ Data sensor diambil otomatis dari endpoint `/iot/latest`
- ✅ Refresh interval: **60 detik** (1 menit)
- ✅ Update otomatis saat component mount (pertama kali load)

### 2. **Display Real-Time Sensor Readings**
- ✅ Tampilan 6 parameter sensor:
  - Suhu (°C)
  - Dissolved Oxygen (mg/L)
  - pH
  - Konduktivitas (µS/cm)
  - Total Coliform Sensor (mV)
  - Status Kelayakan (Gauge)

### 3. **Timestamp Update**
- ✅ Menampilkan waktu update terakhir dari IoT
- ✅ Indikator loading saat memperbarui data

### 4. **Error Handling**
- ✅ Notifikasi jika belum ada data IoT
- ✅ Pesan error yang jelas dan informatif

## 🔄 Alur Kerja Sistem

```
ESP32/Mappi32
    ↓ (setiap 1 jam)
    POST /iot/data
    ↓
Backend API
    ↓ (simpan ke memory)
    ↓
    GET /iot/latest ← Frontend (auto-refresh 60 detik)
    ↓
Dashboard Display
    ↓ (auto-predict)
    POST /predict
    ↓
Tampilkan Hasil & Status Kelayakan
```

## 🎯 Cara Kerja Frontend

### **Saat Halaman Dibuka**
1. Frontend memanggil `fetchLatestIoTData()` pertama kali
2. Mengambil data dari `GET /iot/latest`
3. Update state sensor (temp, DO, pH, conductivity, coliform)
4. Otomatis trigger prediksi AI dengan data terbaru
5. Tampilkan hasil di dashboard

### **Auto-Refresh Berkala**
- Setiap **60 detik**, frontend akan:
  - Fetch data terbaru dari `/iot/latest`
  - Update tampilan sensor
  - Jalankan prediksi ulang
  - Update chart history

### **Jika Belum Ada Data IoT**
- Error message: *"Belum ada data IoT. Pastikan ESP32 sudah mengirim data."*
- Cek apakah ESP32 sudah:
  - ✅ Terhubung ke WiFi
  - ✅ Berhasil POST ke `/iot/data`
  - ✅ Serial Monitor menunjukkan "✓ Data sent successfully!"

## ⚙️ Konfigurasi

### **Mengubah Interval Refresh**
Edit file `frontend_water_quality_dashboard_react.tsx`:

```typescript
// Ubah nilai REFRESH_INTERVAL (dalam milidetik)
const REFRESH_INTERVAL = 60000; // 60 detik (default)

// Contoh untuk 30 detik:
const REFRESH_INTERVAL = 30000;

// Contoh untuk 5 menit:
const REFRESH_INTERVAL = 300000;
```

### **Mengubah API Endpoint**
Edit variabel `API_BASE`:

```typescript
// Untuk production (cloud)
const API_BASE = "https://water-quality-ai-ejw2.onrender.com";

// Untuk testing local
const API_BASE = "http://localhost:8000";

// Atau gunakan environment variable
const API_BASE = import.meta.env.VITE_API_BASE || "https://water-quality-ai-ejw2.onrender.com";
```

## 🧪 Testing

### **1. Test dengan Data Manual (Backend Local)**
Kirim data dummy ke backend:

```bash
# Windows PowerShell
$body = @{
    temp_c = 27.8
    do_mgl = 6.2
    ph = 7.2
    conductivity_uscm = 620
    totalcoliform_mv = 100
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/iot/data" -Method Post -Body $body -ContentType "application/json"
```

### **2. Test Auto-Refresh**
1. Buka browser console (F12)
2. Lihat network tab
3. Setiap 60 detik akan ada request ke `/iot/latest`

### **3. Test Error Handling**
- Stop backend → Frontend akan menampilkan error connection
- Clear data IoT → Frontend akan menampilkan "Belum ada data IoT"

## 📱 User Interface Changes

### **Sebelum (Mode Input Manual)**
- ❌ Form input untuk setiap parameter
- ❌ Button "Prediksi & Evaluasi"
- ❌ Checkbox untuk Total Coliform

### **Sesudah (Mode IoT Monitoring)**
- ✅ Display read-only untuk sensor readings
- ✅ Auto-refresh tanpa interaksi user
- ✅ Timestamp update terakhir
- ✅ Status badge untuk setiap parameter
- ✅ Loading indicator saat refresh

## 🚀 Deployment

### **Backend**
Pastikan backend sudah di-deploy dengan IoT endpoints:
- `POST /iot/data` - Menerima data dari ESP32
- `GET /iot/latest` - Mengambil data terbaru
- `POST /predict` - Prediksi AI

### **Frontend**
```bash
# Build untuk production
npm run build

# Deploy ke hosting (Vercel, Netlify, dll)
# Pastikan environment variable VITE_API_BASE sudah diset
```

## 🔧 Troubleshooting

### **Problem: Data tidak muncul di dashboard**
**Solution:**
1. Cek apakah backend running: `curl http://localhost:8000/iot/latest`
2. Cek apakah ESP32 sudah kirim data: Lihat Serial Monitor
3. Cek browser console untuk error messages

### **Problem: Auto-refresh tidak jalan**
**Solution:**
1. Buka browser console
2. Cek ada error JavaScript atau tidak
3. Pastikan `useEffect` dipanggil (lihat network tab)

### **Problem: Error 404 di /iot/latest**
**Solution:**
- Backend belum ter-update dengan IoT endpoints
- Push perubahan `backend_fastapi.py` ke repository
- Re-deploy backend di Render

### **Problem: Data coliform selalu 0**
**Solution:**
- ESP32 mengirim `totalcoliform_mv` bukan `totalcoliform_mpn_100ml`
- Sensor coliform optional, bisa 0 jika tidak ada

## 📊 Monitoring Dashboard Features

### **Banner Status Kelayakan**
- 🟢 **HIJAU** = Air Layak Minum (Potable)
- 🔴 **MERAH** = Air Tidak Layak Minum (Non-potable)

### **Sensor Cards**
- Real-time readings dengan badge status
- Color-coded indicators:
  - 🟢 Green = Optimal/Normal
  - 🟡 Yellow = Warning/Low
  - 🔴 Red = High/Danger

### **Chart History**
- Area chart untuk trend prediksi
- Confidence interval (CI 90%)
- Max 50 data points history

### **AI Detection Panel**
- Alasan/temuan
- Rekomendasi tindakan
- Alternatif penggunaan air

## 🎯 Next Steps

1. ✅ Deploy backend dengan IoT endpoints ke Render
2. ✅ Upload kode ESP32 ke hardware
3. ✅ Test koneksi ESP32 → Backend
4. ✅ Monitor dashboard untuk data real-time
5. ⏳ Kalibrasi sensor jika diperlukan
6. ⏳ Adjust refresh interval sesuai kebutuhan

## 📞 Support

Jika ada pertanyaan atau masalah:
1. Cek `IOT_SETUP_GUIDE.md` untuk setup ESP32
2. Cek Serial Monitor ESP32 untuk debug
3. Cek browser console untuk error frontend
4. Cek backend logs untuk error API

---

**Last Updated:** November 2, 2025
**Mode:** IoT Real-Time Monitoring
**Refresh Interval:** 60 seconds
**ESP32 Send Interval:** 1 hour (3600 seconds)
