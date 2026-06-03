# AccuTester

Desktopapplicatie voor realtime monitoring van temperatuurmetingen via Arduino en genereren van grafieken uit meetgegevens.

## Functionaliteit

- ✅ Realtime temperatuurmetingen van vier sensoren via seriële COM-poort
- ✅ Realtime weergave van plots met gedeelde y-as
- ✅ CSV-logging van metingen naar `metingen.csv`
- ✅ Vastleggen van testcondities en omgevingstemperatuur
- ✅ Grafiekgeneratie op basis van temperatuur- en elektriciteitsdata
- ✅ Auto-detection Arduino COM-poort
- ✅ Modern UI met PySide6

## Vereisten

- Python 3.11+
- Windows, macOS, of Linux
- Arduino met Tempmeter_arduinoV2 sketch

## Installatie

### 1. Clone repository en navigeer naar project
```bash
cd accutest-gui
```

### 2. Maak virtuele omgeving
```bash
python -m venv venv
```

### 3. Activeer omgeving

**Windows:**
```powershell
venv\Scripts\Activate.ps1
```

**Linux/macOS:**
```bash
source venv/bin/activate
```

### 4. Installeer dependencies
```bash
pip install -r requirements.txt
```

## Gebruik

Start applicatie:
```bash
python run.py
```

Of direct vanuit src:
```bash
cd src
python main.py
```

## Project Structuur

```
accutest-gui/
├── src/
│   ├── main.py              # Entry point
│   ├── main_window.py       # UI-logica
│   ├── config.py            # Configuratie
│   ├── style.py             # Styling
│   ├── icons.py             # SVG-icoontjes
│   ├── graph_maker.py       # Grafiekgeneratie
│   ├── utils.py             # Utilities
│   ├── lazy_loader.py       # Lazy loading
│   └── widgets/             # Aangepaste widgets
│       ├── arrow_combo_box.py
│       ├── browse_button.py
│       ├── file_drop_button.py
│       └── sensor_plot.py
├── assets/
│   └── Logo.ico
├── data/
│   └── test_data/           # Voorbeeld CSV-bestanden
├── tests/
├── run.py                   # Start script
├── AccuTester.spec          # PyInstaller config
├── requirements.txt
└── README.md
```

## Configuratie

Wijzig instellingen in [src/config.py](src/config.py):

```python
BAUD = 115200              # Baud rate
SAMPLE_HZ = 5.0            # Sample frequentie
WINDOW_SECONDS = 2 * 60    # Plot window (2 minuten)
PLOT_UPDATE_HZ = 1.0       # Plot refresh rate
```

## Dependencies

- `PySide6` ≥6.0 - Qt bindings
- `pyqtgraph` ≥0.13 - Realtime plots
- `pyserial` ≥3.5 - Seriële communicatie
- `pandas` ≥1.5 - Data-verwerking
- `matplotlib` ≥3.7 - Grafiekgeneratie

## Hardware Setup

### Arduino Aansluiting

1. Upload `Tempmeter_arduinoV2.ino` naar Arduino
2. Sluit 4× DS18B20 sensoren aan op One-Wire bus (Pin 2)
3. Verbind Arduino via USB naar computer
4. Start AccuTester app

### Sensor Adressen

Zie [arduino/README.md](../arduino/README.md) voor sensor configuratie.

## Build naar EXE (Windows)

```bash
pip install pyinstaller
pyinstaller AccuTester.spec
```

Output: `dist/AccuTester.exe`

## CSV Bestanden

### metingen.csv
```csv
timestamp,sensor1_C,sensor2_C,sensor3_C,sensor4_C
2026-04-29 09:16:00.123,25.42,25.38,25.40,25.39
```

### testcondities.csv
```csv
timestamp,ambient_temp,test_type,notes
2026-04-29 09:16:00,20.5,cooling_test,Initial state
```

## Development

```bash
# Run tests
python -m pytest tests/

# Format code
black src/

# Lint
pylint src/
```

## Licentie

Zie LICENSE file
