# BTMS - BMS Gateway GUI

Python GUI applicatie voor communicatie met BMS (Battery Management System) en BTMS (Battery Thermal Management System) via seriële CAN-interface.

## Functionaliteit

- Realtime monitoring van BMS-statussen
- Thermische beheer controle
- Handmatige temperatuurinstellingen (1-50°C)
- Status weergave met gecodeerde error-levels
- Support voor SVG-icoontjes met dynamische kleuring
- Seriële communicatie via CAN-gateway

## Vereisten

- Python 3.8+
- Tkinter (standaard in Python)
- Seriële apparaat (USB to CAN converter)

## Installatie

1. Zorg dat Python 3.8 of hoger geïnstalleerd is
2. Installeer dependencies:

```bash
pip install -r requirements.txt
```

## Gebruik

Start de applicatie:

```bash
python GUI_BMS_en_BTMS_met_settemp.py
```

## Instellingen

- **BAUDRATE**: 115200 (standaard)
- **MIN_SETTEMP**: 1°C
- **MAX_SETTEMP**: 50°C

## Dependencies

- `pyserial` - Seriële communicatie
- `tksvg` - SVG-ondersteuning in Tkinter
- `Pillow` (PIL) - Afbeeldingsverwerking

## Communicatieprotocol

De applicatie communiceert via een serieel protocol met CAN-gateway:

```
Format: key=value;key=value;...
Voorbeeld: MODE=1;TEMP=25.5;RELAY=1;
```

## Error Codes

- 0: Geen fout
- 1: PTC level 1 fault
- 48: BMS/TMS CAN communication fault
- (zie bron voor volledige lijst)
