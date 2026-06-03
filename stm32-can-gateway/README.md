# STM32 CAN Gateway

STM32F105 based dual CAN bus gateway / isolator.

Designed for a EMUS BMS CAN to NMEA2000 converter.
But hardware can be used for many CAN gateway or CAN isolation applications.

## Specs

- **MCU**: STM32F105RCT6 72MHz met 2 interne CAN controllers
- **CAN1**: BMS (micro-fit 6-pin connector) optioneel geïsoleerd
- **CAN2**: NMEA2000 (M12 5-pin connector) optioneel geïsoleerd of tweede micro-fit 6-pin connector
- **Spanning**: 4-32V
- **Status LED**: RGB
- **Firmware updates**: USB-C

## Hardware Features

- Solder jumpers voor M12 male/female connectoren
- Solder jumpers voor CAN termination resistor
- Solder jumpers voor power output op CAN2 connector

## Pinout

### EMUS BMS micro-fit 6p connector (CAN1 & power input)
- Pin 1: +12V
- Pin 2: CAN1_H
- Pin 3: CAN1_L
- Pin 4: GND
- Pins 5-6: Reserved

### NMEA2000 M12 5p connector (CAN2 & optional power output)
- Pin 1: Shield/GND
- Pin 2: CAN2_L
- Pin 3: CAN2_H
- Pin 4: GND
- Pin 5: +12V (optional, via jumper)

## Projectstructuur

```
stm32-can-gateway/
├── README.md
├── LICENSE
├── images/
│   ├── STM32_CAN_gateway.png
│   └── STM32_CAN_gateway_pinout.png
├── STM32CubeIDE NMEA2000 battery example/
│   ├── Core/              # MCU core code
│   ├── Drivers/           # STM32 HAL drivers
│   ├── Libs/              # NMEA2000 libraries
│   ├── Middlewares/       # Middleware components
│   ├── USB_DEVICE/        # USB configuration
│   └── ...config files
├── Docs/                  # Documentatie
└── LICENSE
```

## Programmering

### STM32CubeIDE Project

Het voorbeeld project is geconfigureerd voor STM32CubeIDE v1.10.1+

**Voor gebruik:**
1. Open STM32CubeIDE
2. File → Import projects from file system
3. Selecteer: `STM32CubeIDE NMEA2000 battery example/`
4. Build en upload naar STM32F105 board

### CAN Configuration

**CAN1 (BMS)**: 
- Baudrate: TBD (zie project)
- Isolated: Optional via jumper

**CAN2 (NMEA2000)**:
- Baudrate: 250kbps (NMEA2000 standard)
- Isolated: Optional via jumper

## Applicaties

- EMUS BMS → NMEA2000 bridge
- CAN bus isolatie/galvanic separation
- Dual CAN monitoring
- NMEA2000 gateway applications

## Support

Zie LICENSE file voor licentie informatie.
