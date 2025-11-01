# 🌊 Setup IoT System - ESP32/Mappi32

## 📋 Daftar Isi
1. [Hardware Requirements](#hardware-requirements)
2. [Software Requirements](#software-requirements)
3. [Wiring Diagram](#wiring-diagram)
4. [Setup ESP32](#setup-esp32)
5. [API Endpoints](#api-endpoints)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

---

## 🔧 Hardware Requirements

### ESP32/Mappi32
- ESP32 Development Board (atau Mappi32)
- Kabel USB untuk programming
- Power supply 5V

### Sensors
✅ **Temperature Sensor**
- DS18B20 (digital, waterproof) RECOMMENDED
- Atau DHT22 (temperature + humidity)
- Range: -55°C to +125°C

✅ **Dissolved Oxygen (DO) Sensor**
- Analog DO sensor (0-20 mg/L)
- Contoh: Gravity Analog DO Sensor
- Output: 0-3.3V analog

✅ **pH Sensor**
- Analog pH sensor (0-14 pH)
- Contoh: DFRobot Analog pH Sensor
- Output: 0-3.3V analog

✅ **Conductivity Sensor**
- TDS/EC Sensor (0-2000 µS/cm)
- Contoh: Gravity TDS Sensor
- Output: 0-3.3V analog

⚠️ **Total Coliform Sensor** (Optional)
- Sensor kimia atau optical
- Output: mV

---

## 💻 Software Requirements

### Arduino IDE
1. Download: https://www.arduino.cc/en/software
2. Install Arduino IDE

### ESP32 Board Support
1. Buka Arduino IDE
2. File → Preferences
3. Tambahkan URL di "Additional Board Manager URLs":
   ```
   https://dl.espressif.com/dl/package_esp32_index.json
   ```
4. Tools → Board → Boards Manager
5. Cari "esp32" dan install

### Libraries
Install via Library Manager (Sketch → Include Library → Manage Libraries):

- **WiFi** (built-in dengan ESP32)
- **HTTPClient** (built-in dengan ESP32)
- **ArduinoJson** (by Benoit Blanchon) ← INSTALL INI!

---

## 📐 Wiring Diagram

### Pinout ESP32/Mappi32

```
ESP32 Pin      →  Sensor
=====================================
GPIO 32        →  Temperature Sensor (Data)
GPIO 33        →  DO Sensor (Analog Out)
GPIO 34        →  pH Sensor (Analog Out)
GPIO 35        →  Conductivity Sensor (Analog Out)
GPIO 36        →  Coliform Sensor (Analog Out) [Optional]

3.3V           →  All Sensors VCC
GND            →  All Sensors GND
```

### Connection Details

#### Temperature Sensor (DS18B20)
```
DS18B20        →  ESP32
Red (VCC)      →  3.3V
Black (GND)    →  GND
Yellow (Data)  →  GPIO 32
```
Note: Butuh pull-up resistor 4.7kΩ antara Data dan VCC

#### DO Sensor
```
DO Sensor      →  ESP32
VCC            →  3.3V
GND            →  GND
Analog Out     →  GPIO 33
```

#### pH Sensor
```
pH Sensor      →  ESP32
VCC            →  3.3V
GND            →  GND
Analog Out     →  GPIO 34
```

#### Conductivity Sensor
```
TDS Sensor     →  ESP32
VCC            →  3.3V
GND            →  GND
Analog Out     →  GPIO 35
```

---

## 🚀 Setup ESP32

### LANGKAH 1: Buka Arduino IDE

1. Buka file `esp32_water_quality.ino`
2. Tools → Board → ESP32 Arduino → "ESP32 Dev Module"
3. Tools → Port → Pilih COM port ESP32 Anda

### LANGKAH 2: Konfigurasi WiFi

Edit baris ini di code:
```cpp
const char* ssid = "YOUR_WIFI_SSID";           // Ganti dengan nama WiFi Anda
const char* password = "YOUR_WIFI_PASSWORD";   // Ganti dengan password WiFi
```

### LANGKAH 3: Konfigurasi API Endpoint

#### Untuk Cloud (Render):
```cpp
const char* apiEndpoint = "https://water-quality-ai-ejw2.onrender.com/iot/data";
```

#### Untuk Testing Lokal:
```cpp
const char* apiEndpoint = "http://192.168.1.100:8000/iot/data";
```
Ganti `192.168.1.100` dengan IP komputer Anda di network lokal.

### LANGKAH 4: Upload Code

1. Hubungkan ESP32 ke komputer via USB
2. Klik tombol "Upload" (→) di Arduino IDE
3. Tunggu hingga selesai
4. Buka Serial Monitor (Tools → Serial Monitor)
5. Set baud rate ke 115200
6. Tekan tombol RESET di ESP32

### LANGKAH 5: Monitor Output

Anda akan lihat di Serial Monitor:
```
=================================
Water Quality Monitoring System
ESP32/Mappi32 IoT Device
=================================

Connecting to WiFi: MyWiFi
............
✓ WiFi Connected!
IP Address: 192.168.1.150
Signal Strength (RSSI): -45 dBm

Setup complete! Starting monitoring...

--- Reading Sensors ---

Sensor Readings:
  Temperature: 27.80 °C
  DO: 6.20 mg/L
  pH: 7.20
  Conductivity: 620.00 µS/cm
  Coliform (mV): 100.00

→ Sending data to API...
  URL: https://water-quality-ai-ejw2.onrender.com/iot/data
  Payload:
  {"temp_c":27.8,"do_mgl":6.2,"ph":7.2,"conductivity_uscm":620,"totalcoliform_mv":100}
  ✓ Response code: 200
  Response:
  {"status":"success","message":"Data received from IoT device"}
  ✓ Data sent successfully!
```

---

## 🔌 API Endpoints

### 1. **POST /iot/data** - Kirim Data dari ESP32
```bash
curl -X POST https://water-quality-ai-ejw2.onrender.com/iot/data \
  -H "Content-Type: application/json" \
  -d '{
    "temp_c": 27.8,
    "do_mgl": 6.2,
    "ph": 7.2,
    "conductivity_uscm": 620,
    "totalcoliform_mv": 100
  }'
```

Response:
```json
{
  "status": "success",
  "message": "Data received from IoT device",
  "data": {
    "timestamp": "2025-11-01T10:30:00",
    "temp_c": 27.8,
    "do_mgl": 6.2,
    "ph": 7.2,
    "conductivity_uscm": 620,
    "totalcoliform_mv": 100
  },
  "total_records": 1
}
```

### 2. **GET /iot/latest** - Ambil Data Terbaru
```bash
curl https://water-quality-ai-ejw2.onrender.com/iot/latest
```

### 3. **GET /iot/history?limit=50** - Ambil History
```bash
curl https://water-quality-ai-ejw2.onrender.com/iot/history?limit=50
```

### 4. **POST /iot/predict** - Auto Predict dari Data Terbaru
```bash
curl -X POST https://water-quality-ai-ejw2.onrender.com/iot/predict
```

### 5. **DELETE /iot/clear** - Clear All Data (Testing)
```bash
curl -X DELETE https://water-quality-ai-ejw2.onrender.com/iot/clear
```

---

## 🧪 Testing

### Test 1: Test WiFi Connection
1. Upload code ke ESP32
2. Buka Serial Monitor
3. Cek apakah dapat IP address
4. Cek RSSI (signal strength) bagus (-70 dBm atau lebih baik)

### Test 2: Test API Connection (Manual)
Gunakan Postman atau curl untuk kirim data test:
```bash
curl -X POST https://water-quality-ai-ejw2.onrender.com/iot/data \
  -H "Content-Type: application/json" \
  -d '{"temp_c":28,"do_mgl":6.5,"ph":7.3,"conductivity_uscm":650,"totalcoliform_mv":110}'
```

### Test 3: Test ESP32 Send Data
1. Tunggu 30 detik (interval default)
2. Cek Serial Monitor untuk log "✓ Data sent successfully!"
3. Buka API `/iot/latest` di browser untuk verify

### Test 4: Test Dashboard
1. Buka dashboard frontend
2. Implementasi auto-refresh setiap 30 detik
3. Data dari ESP32 akan muncul otomatis

---

## 🔧 Sensor Calibration

### pH Sensor Calibration
1. Siapkan buffer solution pH 4.0, 7.0, dan 10.0
2. Celupkan sensor di pH 7.0
3. Catat voltage yang dibaca
4. Adjust `phOffset` di code
5. Test dengan pH 4.0 dan 10.0
6. Adjust `phSlope` jika perlu

### DO Sensor Calibration
1. Siapkan air jenuh oksigen (saturated water)
2. Atau ekspos sensor ke udara terbuka
3. Catat voltage
4. Adjust `doOffset` dan `doSlope`

### Conductivity Calibration
1. Gunakan standard solution (1413 µS/cm)
2. Celupkan sensor
3. Adjust `conductivityOffset` dan `conductivitySlope`

---

## ❌ Troubleshooting

### WiFi tidak connect
- ✅ Cek SSID dan password benar
- ✅ Cek WiFi 2.4GHz (ESP32 tidak support 5GHz)
- ✅ Cek signal strength cukup kuat
- ✅ Restart ESP32 dan router

### Data tidak terkirim (Error 404/500)
- ✅ Cek API endpoint URL benar
- ✅ Test API dengan curl/Postman dulu
- ✅ Cek backend sudah deploy dan running
- ✅ Cek firewall tidak block request

### Sensor reading tidak akurat
- ✅ Cek wiring dan koneksi
- ✅ Lakukan kalibrasi sensor
- ✅ Cek power supply stabil (gunakan external 5V jika perlu)
- ✅ Tambahkan filtering/averaging di code

### ESP32 restart terus (watchdog)
- ✅ Tambahkan `delay()` di loop
- ✅ Jangan blocking terlalu lama
- ✅ Feed watchdog jika proses lama

### HTTP request timeout
- ✅ Cek koneksi internet stabil
- ✅ Increase timeout di HTTPClient
- ✅ Retry logic jika gagal

---

## 📝 Next Steps

1. ✅ Setup hardware sesuai wiring diagram
2. ✅ Upload code ke ESP32
3. ✅ Test koneksi WiFi dan API
4. ✅ Kalibrasi sensor
5. ✅ Update frontend untuk auto-fetch dari `/iot/latest`
6. ✅ Deploy system

---

## 💡 Tips

- **Power Management**: Gunakan deep sleep untuk hemat baterai
- **Data Buffer**: Simpan data di SPIFFS jika offline
- **OTA Update**: Implementasi Over-The-Air update
- **Security**: Gunakan HTTPS dan API key untuk production
- **Monitoring**: Setup alert jika ESP32 offline

---

**Happy Building! 🚀**
