# Stage EV Europe - Accu Conditioning

Projectrepository voor EV-accu conditioning en monitoring systemen. Bevat vier interconnected projecten voor temperatuurmeting, gateway-communicatie en thermisch beheer.

## 📋 Projectoverzicht

| Project | Type | Beschrijving |
|---------|------|-------------|
| **[AccuTester GUI](accutest-gui/)** | Python/PySide6 | Desktop app voor realtime temperatuurmeting en monitoring |
| **[Arduino Tempmeter](arduino/)** | Arduino/C++ | Firmware voor 4× DS18B20 temperatuursensoren |
| **[BTMS - BMS Gateway GUI](btms-bms-gateway-gui/)** | Python/Tkinter | GUI voor BMS en thermisch management systeem |
| **[STM32 CAN Gateway](stm32-can-gateway/)** | STM32/C | CAN-bus gateway met NMEA2000 interface |

## 🏗️ Architectuur

```
┌─────────────────────────────────────────────────────────┐
│                    AccuTester GUI                        │
│              (Monitoring & Grafiekgeneratie)              │
└──────────────────┬──────────────────────────────────────┘
                   │ Serieel (115200 baud)
┌──────────────────▼──────────────────────────────────────┐
│                 Arduino Tempmeter V2                      │
│         (4× DS18B20 temperatuursensoren)                 │
└──────────────────────────────────────────────────────────┘
                   
┌──────────────────────────────────────────────────────────┐
│           BTMS - BMS Gateway GUI                         │
│         (Thermisch beheer & CAN control)                 │
└──────────────────┬──────────────────────────────────────┘
                   │ CAN-bus
┌──────────────────▼──────────────────────────────────────┐
│             STM32 CAN Gateway                            │
│    (EMUS BMS ↔ NMEA2000 converter)                       │
└──────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. AccuTester (Monitoring)
```bash
cd accutest-gui
python -m venv venv
source venv/bin/activate  # of venv\Scripts\Activate.ps1 op Windows
pip install -r requirements.txt
python run.py
```

### 2. Arduino Setup
```bash
# Upload Tempmeter_arduinoV2.ino naar Arduino via Arduino IDE
# Sensors: Sluit 4× DS18B20 aan op Pin 2 (One-Wire bus)
```

### 3. BTMS GUI
```bash
cd btms-bms-gateway-gui
pip install -r requirements.txt
python GUI_BMS_en_BTMS_met_settemp.py
```

### 4. STM32 CAN Gateway
```bash
# Open STM32CubeIDE
# Import: STM32CubeIDE NMEA2000 battery example/
# Build & flash naar STM32F105 board
```

## 📁 Folder Structuur

```
stage-ev-europe-accuconditionering/
│
├── accutest-gui/                      # Desktop monitoring app
│   ├── src/
│   ├── assets/
│   ├── data/
│   ├── tests/
│   ├── requirements.txt
│   ├── README.md
│   └── run.py
│
├── arduino/                           # Arduino firmware
│   ├── Tempmeter_arduinoV2.ino
│   ├── README.md
│   └── ...
│
├── btms-bms-gateway-gui/              # BMS/BTMS control
│   ├── GUI_BMS_en_BTMS_met_settemp.py
│   ├── requirements.txt
│   ├── README.md
│   └── ...
│
├── stm32-can-gateway/                 # CAN gateway hardware
│   ├── STM32CubeIDE NMEA2000 battery example/
│   ├── images/
│   ├── LICENSE
│   ├── README.md
│   └── ...
│
├── README.md                          # Dit bestand
├── .gitignore                         # Git ignore regels
└── LICENSE
```

## 📝 Detaildocumentatie

- **[AccuTester README](accutest-gui/README.md)** - GUI installatie & gebruik
- **[Arduino README](arduino/README.md)** - Firmware & sensor setup
- **[BTMS README](btms-bms-gateway-gui/README.md)** - BMS GUI & protocol
- **[STM32 README](stm32-can-gateway/README.md)** - CAN gateway specs

### Environment Setup
```bash
# Python projects - create virtual environment
python -m venv venv

# Install all dependencies
pip install -r requirements.txt
```

4. Push naar branch (`git push origin feature/improvement`)
5. Open Pull Request

---

**Laatst bijgewerkt**: June 2026
