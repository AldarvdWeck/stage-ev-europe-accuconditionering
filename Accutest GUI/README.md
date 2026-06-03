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

## Projectstructuur

```
EVEGUI/
├── src/                              # Broncode
│   ├── __init__.py
│   ├── main.py                       # Hoofdprogramma (ingang)
│   ├── main_window.py                # Hoofd UI-logica
│   ├── utils.py                      # Hulpprogramma's
│   ├── config.py                     # Configuratiegegevens
│   ├── style.py                      # UI-styling
│   ├── icons.py                      # SVG-icoontjes
│   ├── graph_maker.py                # Grafiekgeneratie
│   └── widgets/                      # Aangepaste UI-widgets
│       ├── __init__.py
│       ├── arrow_combo_box.py
│       ├── browse_button.py
│       ├── file_drop_button.py
│       └── sensor_plot.py
├── assets/                           # Afbeeldingen, icoontjes
│   └── Logo.ico
├── data/                             # Testgegevens
│   └── test_data/
├── tests/                            # Unit-tests
├── docs/                             # Documentatie
├── .gitignore
├── README.md
├── requirements.txt
├── run.py                            # Entry point
└── AccuTester.spec                   # PyInstaller configuratie
```

## Installatie

1. Zorg dat Python 3.11 of hoger geïnstalleerd is.
2. Maak een virtuele omgeving aan:

```bash
python -m venv venv
```

3. Activeer de virtuele omgeving:

Windows:
```powershell
venv\Scripts\Activate.ps1
```

Linux/macOS:
```bash
source venv/bin/activate
```

4. Installeer de dependencies:

```bash
pip install -r requirements.txt
```

## Gebruik

Start de applicatie met:

```bash
python run.py
```

Ofin de src-map:
```bash
cd src
python main.py
```

## GitHub / versiebeheer

Deze repository is voorbereid voor GitHub:

```bash
git remote add origin https://github.com/<gebruikersnaam>/<repositorynaam>.git
git push -u origin master
```

## Dependencies

- `PySide6` - Qt bindings voor Python
- `pyqtgraph` - Real-time grafiekweergave
- `pyserial` - Seriële communicatie met Arduino
- `pandas` - Data-verwerking
- `matplotlib` - Grafieken

## Licentie

[Voeg licentie toe]

