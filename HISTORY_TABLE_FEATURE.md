# 📜 Fitur Tabel Riwayat Data IoT

## 🎯 Overview

Dashboard sekarang dilengkapi dengan **Tabel History** yang menampilkan semua data sensor IoT yang pernah dikirim, lengkap dengan:
- ✅ Timestamp pengiriman
- ✅ Semua parameter sensor (Temp, DO, pH, Konduktivitas, Coliform)
- ✅ **Prediksi AI** untuk setiap data
- ✅ **Status kelayakan** (Layak/Tidak Layak)

## 📊 Fitur Tabel History

### **1. Auto-Load Data**
- Saat dashboard dibuka, otomatis fetch history data
- Menampilkan max **50 data terbaru**
- Auto-refresh setiap 1 jam (mengikuti interval dashboard)

### **2. Manual Refresh**
- Tombol **"🔄 Refresh History"** untuk update manual
- Berguna saat testing dengan data baru

### **3. Prediksi AI Otomatis**
- Setiap data di history akan di-predict menggunakan AI
- Prediksi dilakukan secara parallel untuk performa optimal
- Menampilkan hasil prediksi Total Coliform (MPN/100mL)

### **4. Status Visual**
- **Badge Hijau** = Air Layak Minum (✓ Layak)
- **Badge Merah** = Air Tidak Layak Minum (✗ Tidak Layak)
- Warna prediksi: Hijau jika 0, Merah jika > 0

## 📋 Kolom Tabel

| Kolom | Deskripsi | Format |
|-------|-----------|--------|
| **#** | Nomor urut | 1, 2, 3, ... |
| **Timestamp** | Waktu data diterima | dd/mm/yyyy, hh:mm:ss |
| **Suhu** | Temperature sensor | ##.## °C |
| **DO** | Dissolved Oxygen | ##.## mg/L |
| **pH** | pH level | ##.## |
| **Konduktivitas** | Conductivity | #### µS/cm |
| **Coliform** | Total Coliform sensor | ### mV |
| **Prediksi AI** | AI prediction | ##.## MPN/100mL |
| **Status** | Kelayakan air | Badge (Layak/Tidak Layak) |

## 🔄 Cara Kerja

```
1. User buka dashboard
   ↓
2. useEffect trigger fetchIoTHistory()
   ↓
3. Fetch dari GET /iot/history?limit=50
   ↓
4. Untuk setiap data:
   - POST /predict dengan parameter sensor
   - Simpan hasil prediksi + status kelayakan
   ↓
5. Render tabel dengan semua data
   ↓
6. Auto-refresh setiap 1 jam
```

## 💻 Implementasi Teknis

### **State Management**
```typescript
const [iotHistory, setIotHistory] = useState<any[]>([]);
const [historyLoading, setHistoryLoading] = useState(false);
```

### **Fetch Function**
```typescript
async function fetchIoTHistory() {
  // 1. Fetch history dari API
  const res = await fetch(`${API_BASE}/iot/history?limit=50`);
  const response = await res.json();
  
  // 2. Predict untuk setiap data (parallel)
  const historyWithPredictions = await Promise.all(
    response.data.map(async (item) => {
      const predictRes = await fetch(`${API_BASE}/predict`, {...});
      const predictData = await predictRes.json();
      return {
        ...item,
        prediction: predictData.prediction.total_coliform_mpn_100ml,
        potable: predictData.ai_detection.potable,
      };
    })
  );
  
  setIotHistory(historyWithPredictions);
}
```

### **Auto-Refresh**
```typescript
useEffect(() => {
  fetchLatestIoTData();
  fetchIoTHistory(); // Fetch history juga
  
  const intervalId = setInterval(() => {
    fetchLatestIoTData();
    fetchIoTHistory(); // Auto-refresh history
  }, REFRESH_INTERVAL);
  
  return () => clearInterval(intervalId);
}, []);
```

## 🎨 UI/UX Features

### **Empty State**
Jika belum ada data:
- Icon archive kosong
- Pesan: "Belum ada data history"
- Hint: "Data IoT akan muncul di sini setelah ESP32 mengirim data"

### **Loading State**
Saat fetch data:
- Spinner animation
- Pesan: "Memuat data history..."

### **Table Styling**
- Hover effect pada row (background abu-abu)
- Border antar row untuk readability
- Font mono untuk timestamp
- Badge dengan warna untuk status
- Responsive table dengan horizontal scroll

## 🧪 Testing

### **1. Kirim Multiple Data**
```powershell
# Kirim 5 data dengan variasi
$datasets = @(
    @{temp_c=26.5;do_mgl=7.0;ph=7.0;conductivity_uscm=500;totalcoliform_mv=40},
    @{temp_c=27.8;do_mgl=6.2;ph=7.2;conductivity_uscm=620;totalcoliform_mv=100},
    @{temp_c=28.5;do_mgl=5.8;ph=6.0;conductivity_uscm=700;totalcoliform_mv=150},
    @{temp_c=29.0;do_mgl=5.5;ph=7.5;conductivity_uscm=1600;totalcoliform_mv=120},
    @{temp_c=25.5;do_mgl=7.5;ph=6.8;conductivity_uscm=480;totalcoliform_mv=60}
)

foreach($d in $datasets) {
    $body = $d | ConvertTo-Json
    Invoke-RestMethod -Uri "https://water-quality-ai-ejw2.onrender.com/iot/data" `
        -Method Post -Body $body -ContentType "application/json"
    Start-Sleep -Seconds 1
}
```

### **2. Verifikasi History API**
```powershell
# Cek data history
$history = Invoke-RestMethod -Uri "https://water-quality-ai-ejw2.onrender.com/iot/history?limit=10"
Write-Host "Total records: $($history.total_records)"
$history.data | Format-Table timestamp, temp_c, ph, do_mgl
```

### **3. Test di Browser**
1. Buka `http://localhost:5173`
2. Scroll ke bawah ke section "📜 Riwayat Data IoT"
3. Lihat tabel dengan semua data + prediksi
4. Klik "🔄 Refresh History" untuk update
5. Verifikasi badge status (hijau/merah)

## 🚀 Performance Optimization

### **Parallel Predictions**
```typescript
// ❌ Sequential (lambat)
for (const item of data) {
  const prediction = await predict(item);
}

// ✅ Parallel (cepat)
const predictions = await Promise.all(
  data.map(item => predict(item))
);
```

### **Limit Data**
- Default: 50 data terbaru
- Bisa diubah dengan parameter `?limit=N`
- Mencegah overload saat banyak data

### **Error Handling**
- Jika prediksi gagal untuk 1 data, data lain tetap ditampilkan
- Prediction/Status akan show "-" jika error

## 📱 Responsive Design

- Table dengan horizontal scroll di mobile
- Font size disesuaikan untuk readability
- Timestamp dalam format compact di mobile
- Badge tetap readable di layar kecil

## 🔧 Customization

### **Ubah Limit Data**
```typescript
// Di fungsi fetchIoTHistory(), ubah limit
const res = await fetch(`${API_BASE}/iot/history?limit=100`); // Tampilkan 100 data
```

### **Tambah Kolom**
Tambahkan di thead dan tbody:
```tsx
<th>Kolom Baru</th>
// ...
<td>{item.new_field}</td>
```

### **Ubah Warna Status**
Edit className di badge status:
```tsx
className={item.potable 
  ? 'bg-blue-100 text-blue-700'  // Ubah warna
  : 'bg-orange-100 text-orange-700'
}
```

## 📊 Use Cases

### **1. Monitoring Jangka Panjang**
- Lihat trend data harian/mingguan
- Identifikasi pola anomali
- Analisis performa sensor

### **2. Quality Control**
- Verifikasi semua data yang masuk
- Deteksi data outlier
- Audit trail lengkap

### **3. Reporting**
- Export data untuk laporan (future feature)
- Screenshot tabel untuk dokumentasi
- Backup data lokal

## 🎯 Next Steps

- [ ] Export to CSV/Excel
- [ ] Filter by date range
- [ ] Sort by column
- [ ] Search/filter functionality
- [ ] Pagination untuk data > 50
- [ ] Chart visualization dari history

---

**Last Updated:** November 2, 2025  
**Feature:** History Table with AI Predictions  
**Status:** ✅ Production Ready
