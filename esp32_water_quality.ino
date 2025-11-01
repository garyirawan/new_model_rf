/*
 * Water Quality Monitoring System - ESP32/Mappi32
 * 
 * Sistem IoT untuk monitoring kualitas air real-time
 * Mengirim data sensor ke backend API via WiFi
 * 
 * Hardware Required:
 * - ESP32 / Mappi32
 * - Temperature sensor (DS18B20 atau DHT22)
 * - DO sensor (Dissolved Oxygen)
 * - pH sensor
 * - Conductivity sensor (TDS/EC sensor)
 * - Optional: Total Coliform sensor
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ====== WiFi Configuration ======
const char* ssid = "YOUR_WIFI_SSID";           // Ganti dengan SSID WiFi Anda
const char* password = "YOUR_WIFI_PASSWORD";   // Ganti dengan password WiFi Anda

// ====== API Configuration ======
const char* apiEndpoint = "https://water-quality-ai-ejw2.onrender.com/iot/data";  // Ganti dengan URL API Anda
// Untuk testing lokal gunakan: "http://192.168.1.100:8000/iot/data"

// ====== Sensor Pins ======
#define TEMP_SENSOR_PIN 32      // Pin untuk temperature sensor
#define DO_SENSOR_PIN 33        // Pin untuk DO sensor (analog)
#define PH_SENSOR_PIN 34        // Pin untuk pH sensor (analog)
#define CONDUCTIVITY_PIN 35     // Pin untuk conductivity sensor (analog)
#define COLIFORM_SENSOR_PIN 36  // Pin untuk coliform sensor (optional)

// ====== Timing Configuration ======
const unsigned long SEND_INTERVAL = 3600000;  // Kirim data setiap 1 jam (3600 detik)
unsigned long lastSendTime = 0;

// ====== Sensor Calibration (sesuaikan dengan sensor Anda) ======
// Temperature sensor calibration
float tempOffset = 0.0;

// pH sensor calibration
float phOffset = 0.0;
float phSlope = 3.5;  // Typical value, calibrate untuk sensor Anda

// DO sensor calibration
float doOffset = 0.0;
float doSlope = 1.0;

// Conductivity sensor calibration
float conductivityOffset = 0.0;
float conductivitySlope = 1.0;

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n\n=================================");
  Serial.println("Water Quality Monitoring System");
  Serial.println("ESP32/Mappi32 IoT Device");
  Serial.println("=================================\n");
  
  // Setup sensor pins
  pinMode(TEMP_SENSOR_PIN, INPUT);
  pinMode(DO_SENSOR_PIN, INPUT);
  pinMode(PH_SENSOR_PIN, INPUT);
  pinMode(CONDUCTIVITY_PIN, INPUT);
  pinMode(COLIFORM_SENSOR_PIN, INPUT);
  
  // Connect to WiFi
  connectWiFi();
  
  Serial.println("\nSetup complete! Starting monitoring...\n");
}

void loop() {
  // Check WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected! Reconnecting...");
    connectWiFi();
  }
  
  // Send data at interval
  if (millis() - lastSendTime >= SEND_INTERVAL) {
    readAndSendData();
    lastSendTime = millis();
  }
  
  delay(100);  // Small delay to prevent watchdog issues
}

void connectWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✓ WiFi Connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("Signal Strength (RSSI): ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
  } else {
    Serial.println("\n✗ WiFi Connection Failed!");
    Serial.println("Check your SSID and password");
  }
}

void readAndSendData() {
  Serial.println("\n--- Reading Sensors ---");
  
  // Read all sensors
  float temp = readTemperature();
  float doValue = readDO();
  float ph = readPH();
  float conductivity = readConductivity();
  float coliformMV = readColiformMV();
  
  // Print sensor values
  Serial.println("\nSensor Readings:");
  Serial.printf("  Temperature: %.2f °C\n", temp);
  Serial.printf("  DO: %.2f mg/L\n", doValue);
  Serial.printf("  pH: %.2f\n", ph);
  Serial.printf("  Conductivity: %.2f µS/cm\n", conductivity);
  Serial.printf("  Coliform (mV): %.2f\n", coliformMV);
  
  // Send to API
  sendDataToAPI(temp, doValue, ph, conductivity, coliformMV);
}

float readTemperature() {
  // TODO: Implement your temperature sensor reading
  // Contoh untuk DS18B20 atau DHT22
  
  // Untuk testing, gunakan dummy data + random variation
  float temp = 27.8 + random(-20, 20) / 10.0;
  return temp;
}

float readDO() {
  // Read analog value from DO sensor
  int rawValue = analogRead(DO_SENSOR_PIN);
  
  // Convert to voltage (ESP32 ADC: 0-4095 = 0-3.3V)
  float voltage = rawValue * (3.3 / 4095.0);
  
  // Convert voltage to DO (mg/L) - sesuaikan dengan datasheet sensor
  // Typical formula: DO = (Voltage * Slope) + Offset
  float doValue = (voltage * doSlope) + doOffset;
  
  // Untuk testing gunakan dummy data
  // doValue = 6.2 + random(-10, 10) / 10.0;
  
  return doValue;
}

float readPH() {
  // Read analog value from pH sensor
  int rawValue = analogRead(PH_SENSOR_PIN);
  
  // Convert to voltage
  float voltage = rawValue * (3.3 / 4095.0);
  
  // Convert voltage to pH - sesuaikan dengan kalibrasi sensor
  // Typical formula: pH = 7.0 - ((Voltage - 1.65) / Slope)
  float ph = 7.0 - ((voltage - 1.65) / phSlope);
  
  // Constrain to valid pH range
  ph = constrain(ph, 0.0, 14.0);
  
  // Untuk testing gunakan dummy data
  // ph = 7.2 + random(-5, 5) / 10.0;
  
  return ph;
}

float readConductivity() {
  // Read analog value from conductivity sensor
  int rawValue = analogRead(CONDUCTIVITY_PIN);
  
  // Convert to voltage
  float voltage = rawValue * (3.3 / 4095.0);
  
  // Convert voltage to conductivity (µS/cm) - sesuaikan dengan sensor
  float conductivity = (voltage * conductivitySlope) + conductivityOffset;
  
  // Untuk testing gunakan dummy data
  // conductivity = 620.0 + random(-50, 50);
  
  return conductivity;
}

float readColiformMV() {
  // Read analog value from coliform sensor (optional)
  int rawValue = analogRead(COLIFORM_SENSOR_PIN);
  
  // Convert to millivolts
  float millivolts = rawValue * (3300.0 / 4095.0);
  
  // Untuk testing gunakan dummy data
  // millivolts = 100.0 + random(-20, 20);
  
  return millivolts;
}

void sendDataToAPI(float temp, float doValue, float ph, float conductivity, float coliformMV) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("✗ Cannot send data - WiFi not connected");
    return;
  }
  
  HTTPClient http;
  
  Serial.println("\n→ Sending data to API...");
  Serial.print("  URL: ");
  Serial.println(apiEndpoint);
  
  // Begin HTTP connection
  http.begin(apiEndpoint);
  http.addHeader("Content-Type", "application/json");
  
  // Create JSON payload
  StaticJsonDocument<256> doc;
  doc["temp_c"] = temp;
  doc["do_mgl"] = doValue;
  doc["ph"] = ph;
  doc["conductivity_uscm"] = conductivity;
  doc["totalcoliform_mv"] = coliformMV;
  
  String jsonPayload;
  serializeJson(doc, jsonPayload);
  
  Serial.println("  Payload:");
  Serial.println("  " + jsonPayload);
  
  // Send POST request
  int httpResponseCode = http.POST(jsonPayload);
  
  // Check response
  if (httpResponseCode > 0) {
    Serial.print("  ✓ Response code: ");
    Serial.println(httpResponseCode);
    
    String response = http.getString();
    Serial.println("  Response:");
    Serial.println("  " + response);
    
    if (httpResponseCode == 200) {
      Serial.println("  ✓ Data sent successfully!");
    }
  } else {
    Serial.print("  ✗ Error sending data: ");
    Serial.println(http.errorToString(httpResponseCode));
  }
  
  http.end();
}
