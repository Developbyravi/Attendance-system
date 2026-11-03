/*
 * ==============================================================================
 *  AIoT SmartAttend — ESP8266 NodeMCU 12E + RC522 RFID Reader Firmware
 *  Compatible with FastAPI Backend2 (Port 8002)
 * ==============================================================================
 *
 *  Hardware Specifications:
 *    - Microcontroller: ESP8266 NodeMCU 12E (ESP-12E)
 *    - RFID Transceiver: MFRC522 (RC522) 13.56 MHz SPI
 *    - Target Backend: SmartAttend Backend2 on Port 8002
 *
 *  Wiring Diagram (NodeMCU ESP8266 to RC522):
 *  --------------------------------------------------------------------------
 *  RC522 Pin       NodeMCU Pin       ESP8266 GPIO       Wiring Notes
 *  --------------------------------------------------------------------------
 *  SDA / SS        D8                GPIO15             SPI Slave Select
 *  SCK             D5                GPIO14             SPI Clock
 *  MOSI            D7                GPIO13             SPI Master Out
 *  MISO            D6                GPIO12             SPI Master In
 *  RST             D0                GPIO16             Reset line
 *  3.3V            3V3               3.3V               *DO NOT CONNECT TO 5V*
 *  GND             GND               GND                Common Ground
 *
 *  Optional Status Indicators:
 *  --------------------------------------------------------------------------
 *  Green LED       D1                GPIO5              Check-in Success / Duplicate
 *  Blue LED        D2                GPIO4              Card Assignment Mode / Wi-Fi
 *  Buzzer          D3                GPIO0              Audio Feedback (Active Buzzer)
 *  --------------------------------------------------------------------------
 *  Note: LEDs and Buzzer are completely optional. The sketch functions via
 *  Serial Monitor even if no external LEDs or buzzer are connected.
 * ==============================================================================
 */

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <SPI.h>
#include <MFRC522.h>
#include <ArduinoJson.h>

// ==============================================================================
// 1. NETWORK & BACKEND CONFIGURATION
// ==============================================================================

// Replace with your local 2.4 GHz Wi-Fi credentials
const char* WIFI_SSID     = "YOUR_WIFI_NAME";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// Backend2 Server Address (Use your computer's LAN IP address on port 8002)
// For example: "http://10.73.245.186:8002" or "http://192.168.1.100:8002"
const char* BACKEND_HOST  = "http://10.73.245.186:8002";

// API Endpoint for Hardware RFID Ingestion
const char* INGEST_PATH   = "/api/kiosk/scan";

// Device Identifier
const char* DEVICE_ID     = "GATE-READER-01";

// ==============================================================================
// 2. PIN DEFINITIONS
// ==============================================================================

#define SS_PIN     D8   // GPIO15
#define RST_PIN    D0   // GPIO16
#define LED_GREEN  D1   // GPIO5
#define LED_BLUE   D2   // GPIO4
#define BUZZER     D3   // GPIO0

MFRC522 mfrc522(SS_PIN, RST_PIN);

// ==============================================================================
// 3. SCAN DEBOUNCE & RECONNECT TIMERS
// ==============================================================================

String lastScannedUid = "";
unsigned long lastScanMillis = 0;
const unsigned long SCAN_DEBOUNCE_MS = 2500;  // Ignore immediate duplicate taps for 2.5s

unsigned long lastReconnectMillis = 0;
const unsigned long WIFI_RETRY_MS = 10000;

// ==============================================================================
// 4. AUDIO / VISUAL FEEDBACK HELPERS
// ==============================================================================

void playTone(int frequency, int durationMs) {
  tone(BUZZER, frequency, durationMs);
  delay(durationMs);
  noTone(BUZZER);
}

void signalSuccess() {
  digitalWrite(LED_GREEN, HIGH);
  playTone(2000, 100);
  delay(50);
  playTone(2500, 120);
  digitalWrite(LED_GREEN, LOW);
}

void signalAssignmentCaptured() {
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_BLUE, HIGH);
    playTone(1800, 70);
    digitalWrite(LED_BLUE, LOW);
    delay(60);
  }
}

void signalAlreadyCheckedIn() {
  digitalWrite(LED_GREEN, HIGH);
  playTone(2200, 150);
  delay(100);
  digitalWrite(LED_GREEN, LOW);
}

void signalError() {
  digitalWrite(LED_BLUE, HIGH);
  playTone(600, 250);
  digitalWrite(LED_BLUE, LOW);
}

// ==============================================================================
// 5. FORMAT RFID CARD UID
// ==============================================================================

String formatUid(byte* buffer, byte bufferSize) {
  String uid = "";
  for (byte i = 0; i < bufferSize; i++) {
    if (buffer[i] < 0x10) {
      uid += "0";
    }
    uid += String(buffer[i], HEX);
  }
  uid.toUpperCase();
  return uid;
}

// ==============================================================================
// 6. TRANSMIT SCAN TO FASTAPI BACKEND2
// ==============================================================================

void transmitCardScan(const String& uid) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println(F("[ERROR] Wi-Fi is disconnected. Cannot transmit scan."));
    signalError();
    return;
  }

  WiFiClient client;
  HTTPClient http;

  String url = String(BACKEND_HOST) + INGEST_PATH;

  // Prepare JSON Request Payload
  StaticJsonDocument<256> requestDoc;
  requestDoc["rfid_uid"] = uid;
  requestDoc["device_id"] = DEVICE_ID;

  String requestBody;
  serializeJson(requestDoc, requestBody);

  Serial.println();
  Serial.print(F("[HTTP] POST -> "));
  Serial.println(url);
  Serial.print(F("[HTTP] Payload: "));
  Serial.println(requestBody);

  if (!http.begin(client, url)) {
    Serial.println(F("[ERROR] Could not initialize HTTP client."));
    signalError();
    return;
  }

  http.setTimeout(7000); // 7-second network timeout
  http.addHeader("Content-Type", "application/json");

  int httpCode = http.POST(requestBody);

  if (httpCode <= 0) {
    Serial.print(F("[HTTP ERROR] Failed to connect: "));
    Serial.println(http.errorToString(httpCode));
    http.end();
    signalError();
    return;
  }

  String response = http.getString();
  Serial.print(F("[HTTP] Status: "));
  Serial.println(httpCode);
  Serial.print(F("[HTTP] Response: "));
  Serial.println(response);

  // Parse Backend2 JSON Response
  StaticJsonDocument<1024> responseDoc;
  DeserializationError jsonError = deserializeJson(responseDoc, response);

  if (jsonError) {
    Serial.println(F("[ERROR] Invalid JSON response received from backend."));
    signalError();
    http.end();
    return;
  }

  const char* status = responseDoc["status"] | "";
  const char* mode = responseDoc["mode"] | "";

  // 1. Administrative RFID Assignment Mode
  if (strcmp(status, "assignment_captured") == 0 || strcmp(mode, "assignment") == 0) {
    const char* studentName = responseDoc["student_name"] | "Student";
    Serial.print(F("[ASSIGNMENT] Card captured for: "));
    Serial.println(studentName);
    signalAssignmentCaptured();
  }
  // 2. Duplicate Tap on Same Day
  else if (strcmp(status, "ALREADY_CHECKED_IN") == 0 || strcmp(status, "duplicate") == 0) {
    const char* studentName = responseDoc["student"]["name"] | "Student";
    Serial.print(F("[ATTENDANCE] Already checked in today: "));
    Serial.println(studentName);
    signalAlreadyCheckedIn();
  }
  // 3. New Successful Daily Check-in
  else if (httpCode == 200 && (strcmp(status, "SUCCESS") == 0 || strcmp(status, "success") == 0)) {
    const char* studentName = responseDoc["student"]["name"] | "Student";
    const char* rollNumber  = responseDoc["student"]["roll_number"] | "";
    Serial.println(F("*********************************************"));
    Serial.print(F(" [VERIFIED] Student: "));
    Serial.println(studentName);
    Serial.print(F(" [VERIFIED] Roll No: "));
    Serial.println(rollNumber);
    Serial.println(F("*********************************************"));
    signalSuccess();
  }
  // 4. Unassigned Card (404 Entity Not Found)
  else if (httpCode == 404) {
    Serial.println(F("[WARNING] Card is not assigned to any registered student."));
    signalError();
  }
  // 5. Other Server Responses
  else {
    Serial.println(F("[NOTICE] Server returned non-success response."));
    signalError();
  }

  http.end();
}

// ==============================================================================
// 7. WI-FI CONNECTION HANDLER
// ==============================================================================

void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.println();
  Serial.print(F("[WIFI] Connecting to '"));
  Serial.print(WIFI_SSID);
  Serial.print(F("'"));

  unsigned long started = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - started < 15000) {
    delay(500);
    Serial.print(".");
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println(F("\n[WIFI] Connected successfully!"));
    Serial.print(F("[WIFI] ESP8266 IP Address: "));
    Serial.println(WiFi.localIP());
    digitalWrite(LED_BLUE, HIGH);
    delay(200);
    digitalWrite(LED_BLUE, LOW);
  } else {
    Serial.println(F("\n[WIFI] Connection failed. Will retry in main loop."));
  }
}

// ==============================================================================
// 8. SETUP
// ==============================================================================

void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println();
  Serial.println(F("================================================"));
  Serial.println(F(" SmartAttend AIoT — ESP8266 RFID Hardware Node "));
  Serial.println(F(" Targeted for FastAPI Backend2 (Port 8002)     "));
  Serial.println(F("================================================"));

  // Initialize indicator pins
  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_BLUE, OUTPUT);
  pinMode(BUZZER, OUTPUT);

  digitalWrite(LED_GREEN, LOW);
  digitalWrite(LED_BLUE, LOW);
  noTone(BUZZER);

  // Initialize SPI bus and MFRC522 RFID reader
  SPI.begin();
  mfrc522.PCD_Init();
  delay(100);

  Serial.print(F("[HARDWARE] RC522 Firmware Version: "));
  mfrc522.PCD_DumpVersionToSerial();

  // Connect to Wi-Fi
  connectWiFi();

  Serial.println(F("[SYSTEM] Scanner ready. Tap RFID card to test."));
}

// ==============================================================================
// 9. MAIN SCAN LOOP
// ==============================================================================

void loop() {
  // 1. Maintain Wi-Fi Connectivity
  if (WiFi.status() != WL_CONNECTED && millis() - lastReconnectMillis >= WIFI_RETRY_MS) {
    lastReconnectMillis = millis();
    Serial.println(F("[WIFI] Reconnecting..."));
    WiFi.reconnect();
  }

  // 2. Check for New Card
  if (!mfrc522.PICC_IsNewCardPresent()) {
    delay(30);
    return;
  }

  // 3. Read Card Serial UID
  if (!mfrc522.PICC_ReadCardSerial()) {
    delay(30);
    return;
  }

  // 4. Format UID (e.g., "4847B047")
  String uid = formatUid(mfrc522.uid.uidByte, mfrc522.uid.size);

  Serial.println();
  Serial.print(F("[RFID SCAN] Card UID Detected: "));
  Serial.println(uid);

  unsigned long now = millis();
  bool isDuplicateTap = (uid == lastScannedUid) && (now - lastScanMillis < SCAN_DEBOUNCE_MS);

  if (isDuplicateTap) {
    Serial.println(F("[SCAN] Repeated tap ignored by local debounce filter."));
  } else {
    lastScannedUid = uid;
    lastScanMillis = now;

    // Transmit scan to Backend2
    transmitCardScan(uid);
  }

  // Halt card reading to avoid continuous read cycles
  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();

  delay(100);
}
