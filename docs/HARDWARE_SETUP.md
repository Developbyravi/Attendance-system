# SmartAttend — IoT Hardware Setup & Firmware Guide

## 1. Hardware Bill of Materials (BOM)

| Component | Specification | Quantity | Purpose |
| :--- | :--- | :---: | :--- |
| **NodeMCU 12E** | ESP8266 Wi-Fi Microcontroller (32-bit Tensilica L106 @ 80/160 MHz) | 1 | Edge IoT controller & HTTP client |
| **MFRC522 (RC522)** | 13.56 MHz RFID Reader/Writer (SPI interface) | 1 | Physical student card detection |
| **Mifare RFID Cards/Fobs** | 13.56 MHz Classic 1K Cards | Any | Issued student identification credentials |
| **Green LED** | 3mm / 5mm (with 220Ω resistor) | 1 | Visual check-in success indicator |
| **Blue LED** | 3mm / 5mm (with 220Ω resistor) | 1 | Visual card assignment / Wi-Fi indicator |
| **Active Buzzer** | 5V / 3.3V Active Piezo Buzzer | 1 | Audio feedback for taps |
| **Jumper Wires** | Female-to-Female & Male-to-Female | ~10 | Breadboard / prototype wiring |
| **Micro-USB Cable** | High-speed data cable | 1 | Power & firmware flashing |

---

## 2. Pin Configuration (NodeMCU ESP8266 $\to$ RC522)

```text
  +------------------+                    +------------------+
  |  NodeMCU ESP8266 |                    |   MFRC522 RC522  |
  |                  |                    |                  |
  |             3.3V +------------------->+ 3.3V (VCC)       |
  |              GND +------------------->+ GND              |
  |         D0 (G16) +------------------->+ RST              |
  |         D8 (G15) +------------------->+ SDA (SS)         |
  |         D5 (G14) +------------------->+ SCK              |
  |         D7 (G13) +------------------->+ MOSI             |
  |         D6 (G12) +------------------->+ MISO             |
  +------------------+                    +------------------+
```

| RC522 RFID Pin | NodeMCU Pin | ESP8266 GPIO | Connection Purpose |
| :--- | :--- | :--- | :--- |
| **SDA / SS** | **D8** | GPIO15 | SPI Slave Select |
| **SCK** | **D5** | GPIO14 | SPI Serial Clock |
| **MOSI** | **D7** | GPIO13 | SPI Master Out Slave In |
| **MISO** | **D6** | GPIO12 | SPI Master In Slave Out |
| **RST** | **D0** | GPIO16 | Module Hardware Reset |
| **3.3V** | **3V3** | 3.3V | **CAUTION: Power RC522 from 3.3V ONLY. Connecting to 5V will damage transceiver.** |
| **GND** | **GND** | GND | Common System Ground |

### Status Indicators (Optional)
- **Green LED**: **D1** (GPIO5) via 220Ω resistor $\to$ GND
- **Blue LED**: **D2** (GPIO4) via 220Ω resistor $\to$ GND
- **Active Buzzer**: **D3** (GPIO0) $\to$ GND

---

## 3. Firmware Flashing Guide

1. **Install Arduino IDE**: Download and install Arduino IDE 2.x from [arduino.cc](https://www.arduino.cc/).
2. **Add ESP8266 Board Support**:
   - In Arduino IDE, go to **File $\to$ Preferences**.
   - In *Additional Board Manager URLs*, add:
     ```text
     https://arduino.esp8266.com/stable/package_esp8266com_index.json
     ```
   - Go to **Tools $\to$ Board $\to$ Boards Manager...**, search for `esp8266`, and click **Install** (v3.1.2 or newer).
3. **Install Required Libraries**:
   - Go to **Tools $\to$ Manage Libraries...**.
   - Search for **`MFRC522`** by *GithubCommunity* $\to$ Click **Install**.
   - Search for **`ArduinoJson`** by *Benoit Blanchon* $\to$ Click **Install**.
4. **Open Sketch**:
   - Open [`firmware/esp8266_rfid_reader.ino`](file:///c:/Users/kr293/Downloads/AIIOT/firmware/esp8266_rfid_reader.ino).
5. **Configure Wi-Fi & Server**:
   - Set your 2.4 GHz Wi-Fi SSID and password:
     ```cpp
     const char* WIFI_SSID     = "YOUR_WIFI_NAME";
     const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
     ```
   - Set backend server IP address (e.g. your computer's LAN IP or AWS EC2 domain):
     ```cpp
     const char* BACKEND_HOST  = "http://10.73.245.186:8002"; // Or https://api.yourdomain.com
     ```
6. **Upload**:
   - Select Board: **NodeMCU 1.0 (ESP-12E Module)**.
   - Select Port: Your active USB COM port.
   - Click **Upload** ($\rightarrow$).
   - Open **Serial Monitor** at **115200 baud** to monitor initialization and live RFID taps.
