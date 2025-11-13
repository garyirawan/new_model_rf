# 📝 Logging Guide - Water Quality API

Panduan lengkap tentang sistem logging di Water Quality API dengan timestamp WIB.

---

## 🎯 Fitur Logging

### ✅ Yang Sudah Diimplementasikan:

1. **Timestamp WIB (UTC+7)** - Semua log menggunakan timezone Indonesia
2. **Multi-Handler** - Console dan File logging
3. **Request/Response Logging** - Setiap API call tercatat
4. **Structured Format** - Format yang konsisten dan mudah dibaca
5. **Log Levels** - INFO, WARNING, ERROR
6. **Startup/Shutdown Logging** - Track aplikasi lifecycle
7. **Performance Metrics** - Response time untuk setiap request

---

## 📋 Format Log

### Format Standar:
```
YYYY-MM-DD HH:MM:SS WIB [LEVEL] logger_name - message
```

### Contoh Output:
```
2025-11-13 21:30:45 WIB [INFO] water_quality_api - 🚀 WATER QUALITY API STARTING UP
2025-11-13 21:30:45 WIB [INFO] water_quality_api - ✓ Model loaded successfully
2025-11-13 21:30:46 WIB [INFO] water_quality_api - → POST /predict | Client: 127.0.0.1
2025-11-13 21:30:46 WIB [INFO] water_quality_api - AI Prediction: temp=27.8°C, DO=6.2mg/L, pH=7.2, cond=620µS/cm → Coliform=0.450 MPN/100mL | Severity=safe | Potable=True
2025-11-13 21:30:46 WIB [INFO] water_quality_api - ← POST /predict | Status: 200 | Time: 45.23ms
```

---

## 📂 Log Files

### Lokasi:
```
logs/
└── water_quality_api.log
```

### Karakteristik:
- **Encoding**: UTF-8 (support emoji & special chars)
- **Rotation**: Manual (implementasi log rotation bisa ditambahkan nanti)
- **Persistence**: File tetap ada setelah restart
- **Git**: File log di-ignore (tidak di-commit ke repository)

---

## 🔍 Log Events

### 1. Startup Events
```
============================================================
🚀 WATER QUALITY API STARTING UP
============================================================
Model path: /path/to/model.joblib
Features order path: /path/to/features.txt
Timezone: WIB (UTC+7)
✓ Model loaded successfully
✓ Model type: Random Forest Regressor
============================================================
✓ API READY - Listening for requests
============================================================
```

### 2. HTTP Requests
**Incoming Request:**
```
→ POST /predict | Client: 192.168.1.100
```

**Response:**
```
← POST /predict | Status: 200 | Time: 45.23ms
```

**Error:**
```
✗ POST /predict | Error: Model not loaded | Time: 12.45ms
```

### 3. IoT Data Ingestion
```
📡 IoT Data received: temp=27.8°C, DO=6.2mg/L, pH=7.2, cond=620µS/cm, coliform_mv=50mV → 0.500 MPN/100mL
✓ IoT data stored successfully. Total records: 123
```

### 4. AI Predictions
```
AI Prediction: temp=27.8°C, DO=6.2mg/L, pH=7.2, cond=620µS/cm → Coliform=0.450 MPN/100mL | Severity=safe | Potable=True
```

### 5. Data Operations
**Fetch Latest:**
```
Fetching latest IoT data: timestamp=2025-11-13T21:30:45+07:00
```

**Fetch History:**
```
Fetching IoT history: limit=50, total_records=123
✓ Returning 50 history records
```

**Clear Data:**
```
🗑️ CLEAR REQUEST: Deleting 123 IoT records from storage
✓ All IoT data cleared successfully. 123 records deleted.
```

### 6. Warnings
```
⚠️ No IoT data available - storage is empty
⚠️ No IoT history data available
```

### 7. Errors
```
✗ Failed to store IoT data: Connection timeout
✗ Failed to load model: File not found
```

### 8. Shutdown Events
```
============================================================
🛑 WATER QUALITY API SHUTTING DOWN
Total data stored: 123 records
============================================================
```

---

## 🎨 Log Symbols

| Symbol | Meaning | Level |
|--------|---------|-------|
| 🚀 | Startup | INFO |
| ✓ | Success | INFO |
| → | Incoming Request | INFO |
| ← | Successful Response | INFO |
| ✗ | Error/Failed | ERROR |
| ⚠️ | Warning | WARNING |
| 📡 | IoT Data | INFO |
| 🗑️ | Delete Operation | WARNING |
| 🛑 | Shutdown | INFO |

---

## 💻 Development Usage

### Melihat Log Real-time (Console):
```bash
# Jalankan API (log akan muncul di console)
python backend_fastapi.py

# Atau dengan uvicorn
uvicorn backend_fastapi:app --reload
```

### Melihat Log File:
```bash
# Windows PowerShell
Get-Content logs/water_quality_api.log -Tail 50 -Wait

# Linux/Mac
tail -f logs/water_quality_api.log

# Cari error di log
Select-String -Path logs/water_quality_api.log -Pattern "ERROR"
```

---

## 🚀 Production Usage (Hugging Face Spaces)

### Log di Hugging Face Spaces:

1. **Console Logs** tersedia di Spaces UI:
   ```
   Settings → Logs tab
   ```

2. **File Logs** tersimpan persistent (selama Space berjalan):
   ```
   logs/water_quality_api.log
   ```

3. **Download Logs** via API (bisa diimplementasikan):
   ```python
   @app.get("/logs/download")
   def download_logs():
       return FileResponse("logs/water_quality_api.log")
   ```

---

## 🔧 Advanced Configuration

### Custom Log Level:
```python
# Di setup_logger()
logger.setLevel(logging.DEBUG)  # More verbose
logger.setLevel(logging.WARNING)  # Less verbose
```

### Log Rotation (Implementasi Future):
```python
from logging.handlers import RotatingFileHandler

file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5  # Keep 5 backup files
)
```

### JSON Logs (Implementasi Future):
```python
import json

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module
        }
        return json.dumps(log_data)
```

---

## 📊 Log Analysis

### Analisis Performance:
```bash
# Cari request lambat (>100ms)
Select-String -Path logs/water_quality_api.log -Pattern "Time: [0-9]{3,}" | Select-String -Pattern "ms"

# Count error
(Select-String -Path logs/water_quality_api.log -Pattern "ERROR").Count

# Stats per endpoint
Select-String -Path logs/water_quality_api.log -Pattern "POST /predict" | Measure-Object
```

### Monitoring Script (PowerShell):
```powershell
# Monitor errors real-time
Get-Content logs/water_quality_api.log -Wait | Where-Object { $_ -match "ERROR" }

# Daily summary
$today = Get-Date -Format "yyyy-MM-dd"
$logs = Get-Content logs/water_quality_api.log | Where-Object { $_ -match $today }

$totalRequests = ($logs | Where-Object { $_ -match "→" }).Count
$totalErrors = ($logs | Where-Object { $_ -match "ERROR" }).Count
$avgTime = ($logs | Where-Object { $_ -match "Time:" } | ForEach-Object {
    if ($_ -match "Time: (\d+\.\d+)ms") { [float]$matches[1] }
} | Measure-Object -Average).Average

Write-Host "📊 Daily Summary ($today)"
Write-Host "Total Requests: $totalRequests"
Write-Host "Total Errors: $totalErrors"
Write-Host "Avg Response Time: $([math]::Round($avgTime, 2))ms"
```

---

## 🛠️ Troubleshooting

### Log File Tidak Terbuat:
```python
# Check permissions
import os
os.makedirs("logs", exist_ok=True)

# Check dalam log warning message
logger.warning(f"Could not create log file: {e}")
```

### Duplicate Log Messages:
```python
# Pastikan logger tidak di-setup multiple times
if logger.handlers:
    return logger  # Already configured
```

### Timezone Salah:
```python
# Verify WIB configuration
WIB = timezone(timedelta(hours=7))  # UTC+7

# Test
print(datetime.now(WIB).strftime('%Y-%m-%d %H:%M:%S %Z'))
```

---

## 📌 Best Practices

### ✅ DO:
- Log semua incoming requests
- Log errors dengan stack trace
- Log important state changes
- Use appropriate log levels
- Include context (request ID, user, etc.)

### ❌ DON'T:
- Log sensitive data (passwords, API keys)
- Log di setiap loop iteration (bisa spam)
- Use print() instead of logger
- Log redundant information
- Leave debug logs di production

---

## 📞 Support

Jika ada masalah dengan logging:
1. Check console output untuk immediate errors
2. Check log file: `logs/water_quality_api.log`
3. Verify timezone: Should be WIB (UTC+7)
4. Check file permissions untuk log directory

---

**Happy Logging! 📝**
