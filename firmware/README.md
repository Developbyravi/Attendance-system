# SmartAttend ESP8266 + MFRC522 Hardware Gateway

This directory contains the production Arduino C++ firmware for the **NodeMCU ESP8266 + MFRC522** RFID reader gateway.

---

## 1. Hardware Pinout Wiring

| MFRC522 Pin | NodeMCU ESP8266 Pin | ESP8266 GPIO | Notes |
|:---|:---|:---|:---|
| **SDA (SS)** | **D4** (or D8) | GPIO2 / GPIO15 | Chip Select SPI |
| **SCK** | **D5** | GPIO14 | SPI Clock |
| **MOSI** | **D7** | GPIO13 | Master Out Slave In |
| **MISO** | **D6** | GPIO12 | Master In Slave Out |
| **RST** | **D3** | GPIO0 | Reset pin |
| **GND** | **GND** | GND | Common Ground |
| **3.3V** | **3V3** | 3.3V | ⚠️ **DO NOT CONNECT TO 5V** (will damage MFRC522) |
| Green LED (opt) | **D1** | GPIO5 | Daily Ingress Verified indicator |
| Blue LED (opt) | **D2** | GPIO4 | Card Assignment Mode Captured indicator |
| Buzzer (opt) | **D0** | GPIO16 | Acoustic tone feedback |

---

## 2. Arduino IDE Setup & Required Libraries

Install the following libraries via **Arduino IDE Library Manager** (`Ctrl+Shift+I`):
1. **MFRC522** (by GithubCommunity, v1.4.10+)
2. **ArduinoJson** (by Benoit Blanchon, v6.21.0+)
3. **ESP8266WiFi** & **ESP8266HTTPClient** (included with ESP8266 Arduino Core)

### Board Manager Configuration
- Add Board URL: `http://arduino.esp8266.com/stable/package_esp8266com_index.json`
- Select: **NodeMCU 1.0 (ESP-12E Module)**
- CPU Frequency: **80 MHz** (or 160 MHz)
- Upload Speed: **115200** or **921600**

---

## 3. Dual-Mode Operation

### Mode A: Daily Campus Ingress Check-in (Default)
- When a student taps an active badge, the reader sends an HTTP POST request to `/api/kiosk/scan` or `/api/rfid/scan`.
- Backend checks the active student record and records today's daily check-in.
- Green LED flashes, tone beeps, and display confirms attendance.

### Mode B: Card Assignment Mode (Admin Initiated)
- Initiated from the **Admin Student Directory** (`/admin/students` -> *Assign RFID*).
- An assignment session is armed on the designated reader (e.g. `GATE-READER-01`).
- When a card is tapped while this session is active:
  - The backend catches the tap into the assignment session buffer.
  - **Attendance is NOT marked**.
  - Reader flashes Blue LED and chirps distinct assignment tone.
  - The Admin UI reveals the verified real physical UID and prompts the admin for final confirmation.

---

## 4. Security & Device Authentication
- Ingress requests must provide the device secret header:
  ```http
  X-Device-API-Key: smartattend-esp32-secret-key-2026
  ```
- Unauthorized devices without valid credentials will receive HTTP 401 Unauthorized.
