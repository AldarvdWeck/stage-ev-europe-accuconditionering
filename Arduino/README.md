# Arduino Tempmeter V2

Arduino sketch voor het uitlezen van vier Dallas DS18B20 temperatuursensoren en verzenden via seriële communicatie (115200 baud).

## Hardware

- **MCU**: Arduino (met seriële communicatie)
- **Sensoren**: 4× Dallas DS18B20 1-Wire temperatuursensoren
- **Display**: 16×2 LCD (via standaard I2C/parallel verbinding)
- **One-Wire Bus**: Pin 2

## Eigenschappen

- Realtime temperatuurmetingen van 4 sensoren
- LCD-display feedback (initialisatie, sensor-telemetry)
- Seriele output op 115200 baud
- Temperatuurcalibratie per sensor (gain-factor)
- Foutdetectie (disconnected/out-of-range sensoren)
- 200ms meet-interval

## Sensor Adressen

Fixed device addresses in code:
```cpp
Sensor 1: {0x28, 0xF0, 0xEA, 0x57, 0x04, 0xE1, 0x3C, 0x67}
Sensor 2: {0x28, 0x7E, 0xAE, 0x57, 0x04, 0xE1, 0x3C, 0x68}
Sensor 3: {0x28, 0x65, 0x2C, 0x57, 0x04, 0xE1, 0x3C, 0x83}
Sensor 4: {0x28, 0xBD, 0x20, 0x57, 0x04, 0xE1, 0x3C, 0xC7}
```

## Kalibratie

Gain-factors per sensor:
```cpp
Sensor 1: 0.99305
Sensor 2: 0.99900
Sensor 3: 0.99206
Sensor 4: 0.99900
```

## Serieel Communicatie

**Output Format**: `T,<temp1>,<temp2>,<temp3>,<temp4>`

Voorbeeld:
```
T,25.42,25.38,25.40,25.39
T,25.43,25.39,25.41,25.40
```

- NaN geeft aan: sensor disconnected of out-of-range
- Temperatuur bereik: -100°C tot 150°C (values outside ignored)

## Installatie

1. Open `Tempmeter_arduinoV2.ino` in Arduino IDE
2. Selecteer het juiste board en COM-port
3. Upload naar Arduino

## Libraries Vereist

- `OneWire` (Paul Stoffregen)
- `DallasTemperature` (Miles Burton)
- `LiquidCrystal` (standaard)

## LCD Display Layout

```
T1:25.4 T2:25.3
T3:25.4 T4:25.4
```

Waar: T1/T2 = bovenrij, T3/T4 = onderrij
