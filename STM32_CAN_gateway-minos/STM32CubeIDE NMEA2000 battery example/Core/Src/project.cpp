/*
 * project.cpp
 * EMUS BMS CAN1 logger + TKT BTMS CAN2 gateway met STM32 HAL
 *
 * CAN1:
 * - EMUS BMS uitlezen
 * - Elke 500 ms request frames sturen
 * - Responses decoderen
 *
 * CAN2:
 * - TKT BTMS statusframes uitlezen
 * - Elke 1000 ms command frame sturen
 *
 * Logica:
 * T < 22 °C      → verwarmen, set_temp = T + 20
 * 22–28 °C      → shutdown, set_temp = 25
 * T > 28 °C     → koelen, set_temp = T - 20
 */

#include "project.hpp"
#include "main.h"

#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>

extern "C"
{
#include "usbd_cdc_if.h"
}
extern "C" uint8_t CDC_Transmit_FS(uint8_t *Buf, uint16_t Len);

extern CAN_HandleTypeDef hcan1;
extern CAN_HandleTypeDef hcan2;


// ============================================================================
// CAN IDs
// ============================================================================

// EMUS BMS CAN1 IDs zoals in CAN1.py
static const uint32_t BMS_BASE_ID    = 0x19B50000;
static const uint32_t BMS_ID_STATUS  = BMS_BASE_ID + 0x0000;
static const uint32_t BMS_ID_VOLTAGE = BMS_BASE_ID + 0x0009;
static const uint32_t BMS_ID_TEMP    = BMS_BASE_ID + 0x0008;

// TKT BTMS CAN2 IDs
static const uint32_t BTMS_COMMAND_ID = 0x18FF45F4;  // controller -> BTMS
static const uint32_t BTMS_STATUS_ID  = 0x18FFC13A;  // BTMS -> controller


// ============================================================================
// Algemene debug variabelen
// ============================================================================

volatile uint32_t can1_init_ok = 0;
volatile uint32_t can2_init_ok = 0;
volatile uint32_t can_init_error = 0;

volatile uint32_t usb_tx_count = 0;
volatile uint32_t usb_tx_error_count = 0;
volatile uint32_t usb_last_tx_ms = 0;


// ============================================================================
// CAN1 / BMS debug variabelen
// ============================================================================

volatile uint32_t can_request_count = 0;
volatile uint32_t can_tx_error_count = 0;
volatile uint32_t can_rx_count = 0;
volatile uint32_t can_unknown_count = 0;

volatile uint32_t last_rx_id = 0;
volatile uint8_t  last_rx_len = 0;
volatile uint8_t  last_rx_data0 = 0;
volatile uint8_t  last_rx_data1 = 0;
volatile uint8_t  last_rx_data2 = 0;
volatile uint8_t  last_rx_data3 = 0;
volatile uint8_t  last_rx_data4 = 0;
volatile uint8_t  last_rx_data5 = 0;
volatile uint8_t  last_rx_data6 = 0;
volatile uint8_t  last_rx_data7 = 0;

volatile int16_t bms_min_temp_c = 0;
volatile int16_t bms_max_temp_c = 0;
volatile int16_t bms_avg_temp_c = 0;
volatile uint32_t temp_rx_count = 0;

volatile uint16_t bms_min_cell_mv = 0;
volatile uint16_t bms_max_cell_mv = 0;
volatile uint16_t bms_avg_cell_mv = 0;
volatile uint32_t bms_pack_mv = 0;
volatile uint32_t voltage_rx_count = 0;

volatile uint16_t bms_live_cells = 0;
volatile uint8_t  bms_charge_stage = 0;
volatile uint16_t bms_charge_time_min = 0;
volatile uint32_t status_rx_count = 0;

volatile uint32_t last_rx_ms = 0;
volatile uint32_t last_request_ms_debug = 0;
volatile uint32_t last_bms_temp_rx_ms = 0;


// ============================================================================
// CAN2 / BTMS RX debug variabelen
// ============================================================================

volatile uint32_t btms_rx_count = 0;
volatile uint32_t btms_unknown_count = 0;
volatile uint32_t btms_last_rx_ms = 0;

volatile uint32_t btms_last_rx_id = 0;
volatile uint8_t  btms_last_rx_len = 0;
volatile uint8_t  btms_last_rx_data0 = 0;
volatile uint8_t  btms_last_rx_data1 = 0;
volatile uint8_t  btms_last_rx_data2 = 0;
volatile uint8_t  btms_last_rx_data3 = 0;
volatile uint8_t  btms_last_rx_data4 = 0;
volatile uint8_t  btms_last_rx_data5 = 0;
volatile uint8_t  btms_last_rx_data6 = 0;
volatile uint8_t  btms_last_rx_data7 = 0;

// Gedecodeerde BTMS status
volatile uint8_t btms_mode = 0;
volatile uint8_t btms_relay_status = 0;

volatile int16_t btms_tout_c = 0;
volatile int16_t btms_tin_c = 0;
volatile int16_t btms_tamb_c = 0;

volatile uint16_t btms_demand_power_x10_kw = 0;

volatile uint8_t btms_error_code = 0;
volatile uint8_t btms_error_level = 0;


// ============================================================================
// CAN2 / BTMS TX debug variabelen
// ============================================================================

volatile uint32_t btms_tx_count = 0;
volatile uint32_t btms_tx_error_count = 0;
volatile uint32_t btms_last_tx_ms = 0;

volatile uint8_t btms_life_frame = 0;

volatile uint8_t btms_command_mode = 0;
volatile uint8_t btms_command_hv_request = 0;
volatile uint8_t btms_command_charging = 0;
volatile uint8_t btms_command_relay = 1;

volatile int16_t btms_command_set_temp_c = 25;
volatile uint16_t btms_command_pack_voltage_v = 340;

volatile uint8_t btms_using_bms_logic = 0;

volatile uint8_t btms_manual_control_enabled = 0;
volatile uint8_t btms_manual_mode = 0;
volatile int16_t btms_manual_set_temp_c = 25;
volatile uint32_t usb_rx_count = 0;
volatile uint32_t usb_command_count = 0;
volatile uint32_t usb_command_error_count = 0;


// ============================================================================
// CAN filters
// ============================================================================

static void can1_accept_all_filter(void)
{
    CAN_FilterTypeDef filter = {0};

    filter.FilterBank = 0;
    filter.FilterMode = CAN_FILTERMODE_IDMASK;
    filter.FilterScale = CAN_FILTERSCALE_32BIT;

    filter.FilterIdHigh = 0x0000;
    filter.FilterIdLow = 0x0000;
    filter.FilterMaskIdHigh = 0x0000;
    filter.FilterMaskIdLow = 0x0000;

    filter.FilterFIFOAssignment = CAN_RX_FIFO0;
    filter.FilterActivation = ENABLE;

    // Filterbanks 0 t/m 13 voor CAN1, 14 t/m 27 voor CAN2
    filter.SlaveStartFilterBank = 14;

    if (HAL_CAN_ConfigFilter(&hcan1, &filter) != HAL_OK)
    {
        can_init_error = 1;
    }
}

static void can2_accept_all_filter(void)
{
    CAN_FilterTypeDef filter = {0};

    filter.FilterBank = 14;
    filter.FilterMode = CAN_FILTERMODE_IDMASK;
    filter.FilterScale = CAN_FILTERSCALE_32BIT;

    filter.FilterIdHigh = 0x0000;
    filter.FilterIdLow = 0x0000;
    filter.FilterMaskIdHigh = 0x0000;
    filter.FilterMaskIdLow = 0x0000;

    filter.FilterFIFOAssignment = CAN_RX_FIFO1;
    filter.FilterActivation = ENABLE;

    filter.SlaveStartFilterBank = 14;

    if (HAL_CAN_ConfigFilter(&hcan2, &filter) != HAL_OK)
    {
        can_init_error = 3;
    }
}

static void can_start_all(void)
{
    can1_accept_all_filter();
    can2_accept_all_filter();

    if (HAL_CAN_Start(&hcan1) != HAL_OK)
    {
        can_init_error = 2;
        can1_init_ok = 0;
    }
    else
    {
        can1_init_ok = 1;
    }

    if (HAL_CAN_Start(&hcan2) != HAL_OK)
    {
        can_init_error = 4;
        can2_init_ok = 0;
    }
    else
    {
        can2_init_ok = 1;
    }
}


// ============================================================================
// CAN1 / BMS requests sturen
// ============================================================================

static void send_bms_request(uint32_t arb_id)
{
    CAN_TxHeaderTypeDef tx_header = {0};
    uint32_t tx_mailbox;
    uint8_t data[8] = {0};

    tx_header.StdId = 0;
    tx_header.ExtId = arb_id;
    tx_header.IDE = CAN_ID_EXT;
    tx_header.RTR = CAN_RTR_DATA;
    tx_header.DLC = 0;
    tx_header.TransmitGlobalTime = DISABLE;

    if (HAL_CAN_AddTxMessage(&hcan1, &tx_header, data, &tx_mailbox) == HAL_OK)
    {
        can_request_count++;
    }
    else
    {
        can_tx_error_count++;
    }
}

static void send_all_bms_requests(void)
{
    send_bms_request(BMS_ID_STATUS);
    send_bms_request(BMS_ID_VOLTAGE);
    send_bms_request(BMS_ID_TEMP);
}


// ============================================================================
// CAN1 / BMS decode functies
// ============================================================================

static void decode_bms_temperature(const uint8_t *data)
{
    bms_min_temp_c = (int16_t)data[0] - 100;
    bms_max_temp_c = (int16_t)data[1] - 100;
    bms_avg_temp_c = (int16_t)data[2] - 100;

    temp_rx_count++;
    last_bms_temp_rx_ms = HAL_GetTick();
}

static void decode_bms_voltage(const uint8_t *data)
{
    bms_min_cell_mv = 2000 + ((uint16_t)data[0] * 10);
    bms_max_cell_mv = 2000 + ((uint16_t)data[1] * 10);
    bms_avg_cell_mv = 2000 + ((uint16_t)data[2] * 10);

    uint32_t raw_pack =
        ((uint32_t)data[3] << 24) |
        ((uint32_t)data[4] << 16) |
        ((uint32_t)data[5] << 8)  |
        ((uint32_t)data[6]);

    bms_pack_mv = raw_pack * 10;

    voltage_rx_count++;
}

static void decode_bms_status(const uint8_t *data)
{
    bms_live_cells = ((uint16_t)data[2] << 8) | data[7];
    bms_charge_stage = data[3];
    bms_charge_time_min = ((uint16_t)data[4] << 8) | data[5];

    status_rx_count++;
}

static void store_bms_raw_frame(uint32_t id, uint8_t len, const uint8_t *data)
{
    last_rx_id = id;
    last_rx_len = len;

    last_rx_data0 = (len > 0) ? data[0] : 0;
    last_rx_data1 = (len > 1) ? data[1] : 0;
    last_rx_data2 = (len > 2) ? data[2] : 0;
    last_rx_data3 = (len > 3) ? data[3] : 0;
    last_rx_data4 = (len > 4) ? data[4] : 0;
    last_rx_data5 = (len > 5) ? data[5] : 0;
    last_rx_data6 = (len > 6) ? data[6] : 0;
    last_rx_data7 = (len > 7) ? data[7] : 0;
}

static void process_bms_frame(uint32_t id, uint8_t len, uint8_t *data)
{
    can_rx_count++;
    last_rx_ms = HAL_GetTick();

    store_bms_raw_frame(id, len, data);

    if (id == BMS_ID_TEMP && len >= 3)
    {
        decode_bms_temperature(data);
    }
    else if (id == BMS_ID_VOLTAGE && len >= 8)
    {
        decode_bms_voltage(data);
    }
    else if (id == BMS_ID_STATUS && len >= 8)
    {
        decode_bms_status(data);
    }
    else
    {
        can_unknown_count++;
    }
}

static void read_can1_bms(void)
{
    CAN_RxHeaderTypeDef rx_header;
    uint8_t data[8];

    while (HAL_CAN_GetRxFifoFillLevel(&hcan1, CAN_RX_FIFO0) > 0)
    {
        if (HAL_CAN_GetRxMessage(&hcan1, CAN_RX_FIFO0, &rx_header, data) == HAL_OK)
        {
            uint32_t id = (rx_header.IDE == CAN_ID_EXT) ? rx_header.ExtId : rx_header.StdId;
            process_bms_frame(id, rx_header.DLC, data);
        }
    }
}


// ============================================================================
// BTMS command logica
// ============================================================================

static int16_t clamp_btms_set_temp(int16_t value)
{
    if (value < 1)
    {
        return 1;
    }

    if (value > 50)
    {
        return 50;
    }

    return value;
}

static uint8_t bms_temperature_is_valid(void)
{
    if (temp_rx_count == 0)
    {
        return 0;
    }

    if ((HAL_GetTick() - last_bms_temp_rx_ms) > 3000)
    {
        return 0;
    }

    return 1;
}

static int16_t clamp_int16(int16_t value, int16_t min_value, int16_t max_value)
{
    if (value < min_value)
    {
        return min_value;
    }

    if (value > max_value)
    {
        return max_value;
    }

    return value;
}

static void update_btms_command(void)
{
    btms_command_hv_request = 0;        // HV Request ON
    btms_command_charging = 0;          // Non-charging
    btms_command_relay = 1;             // Relay CLOSED
    btms_command_pack_voltage_v = 340;

    btms_using_bms_logic = 0;
    btms_command_mode = 0;              // Shutdown
    btms_command_set_temp_c = 25;

    if (btms_manual_control_enabled)
    {
        btms_command_mode = btms_manual_mode;
        btms_command_set_temp_c = clamp_btms_set_temp(btms_manual_set_temp_c);
        return;
    }

    if (!bms_temperature_is_valid())
    {
        btms_command_mode = 0;
        btms_command_set_temp_c = 25;
        return;
    }

    btms_using_bms_logic = 1;

    int16_t temp = bms_avg_temp_c;
    int16_t set_temp = 25;

    if (temp < 22)
    {
        // Accu is koud: Heating
        btms_command_mode = 2;

        // Verwarmen met maximaal 20 °C boven de accutemperatuur
        set_temp = temp + 20;
    }
    else if (temp > 28)
    {
        // Accu is warm: Cooling
        btms_command_mode = 1;

        // Koelen met maximaal 20 °C onder de accutemperatuur
        set_temp = temp - 20;
    }
    else
    {
        // Tussen 22 en 28 graden: Shutdown
        btms_command_mode = 0;
        set_temp = 25;
    }

    btms_command_set_temp_c = clamp_btms_set_temp(set_temp);

    btms_manual_set_temp_c = btms_command_set_temp_c;
}

static void send_btms_command(void)
{
    CAN_TxHeaderTypeDef tx_header = {0};
    uint32_t tx_mailbox;
    uint8_t data[8] = {0};

    update_btms_command();

    data[0] =
        (btms_command_mode & 0x03) |
        ((btms_command_hv_request & 0x03) << 2) |
        ((btms_command_charging & 0x03) << 4) |
        ((btms_command_relay & 0x03) << 6);

    data[1] = (btms_command_pack_voltage_v >> 8) & 0xFF;
    data[2] = btms_command_pack_voltage_v & 0xFF;

    data[3] = 0x00;

    data[4] = (uint8_t)(btms_command_set_temp_c + 40);

    data[5] = 0x00;

    data[6] = btms_life_frame & 0xFF;
    btms_life_frame++;

    data[7] = 0x00;

    tx_header.StdId = 0;
    tx_header.ExtId = BTMS_COMMAND_ID;
    tx_header.IDE = CAN_ID_EXT;
    tx_header.RTR = CAN_RTR_DATA;
    tx_header.DLC = 8;
    tx_header.TransmitGlobalTime = DISABLE;

    if (HAL_CAN_AddTxMessage(&hcan2, &tx_header, data, &tx_mailbox) == HAL_OK)
    {
        btms_tx_count++;
        btms_last_tx_ms = HAL_GetTick();
    }
    else
    {
        btms_tx_error_count++;
    }
}


// ============================================================================
// CAN2 / BTMS status decode
// ============================================================================

static void decode_btms_status(const uint8_t *data)
{
    btms_mode = data[0] & 0x03;
    btms_relay_status = (data[0] >> 2) & 0x03;

    btms_tout_c = (int16_t)data[1] - 40;
    btms_tin_c  = (int16_t)data[2] - 40;
    btms_tamb_c = (int16_t)data[3] - 40;

    btms_demand_power_x10_kw =
        ((uint16_t)data[5] << 8) |
        ((uint16_t)data[6]);

    btms_error_code = data[7] & 0x3F;
    btms_error_level = (data[7] >> 6) & 0x03;
}

static void store_btms_raw_frame(uint32_t id, uint8_t len, const uint8_t *data)
{
    btms_last_rx_id = id;
    btms_last_rx_len = len;

    btms_last_rx_data0 = (len > 0) ? data[0] : 0;
    btms_last_rx_data1 = (len > 1) ? data[1] : 0;
    btms_last_rx_data2 = (len > 2) ? data[2] : 0;
    btms_last_rx_data3 = (len > 3) ? data[3] : 0;
    btms_last_rx_data4 = (len > 4) ? data[4] : 0;
    btms_last_rx_data5 = (len > 5) ? data[5] : 0;
    btms_last_rx_data6 = (len > 6) ? data[6] : 0;
    btms_last_rx_data7 = (len > 7) ? data[7] : 0;
}

static void process_btms_frame(uint32_t id, uint8_t len, uint8_t *data)
{
    btms_rx_count++;
    btms_last_rx_ms = HAL_GetTick();

    store_btms_raw_frame(id, len, data);

    if (id == BTMS_STATUS_ID && len >= 8)
    {
        decode_btms_status(data);
    }
    else
    {
        btms_unknown_count++;
    }
}

static void read_can2_btms(void)
{
    CAN_RxHeaderTypeDef rx_header;
    uint8_t data[8];

    while (HAL_CAN_GetRxFifoFillLevel(&hcan2, CAN_RX_FIFO1) > 0)
    {
        if (HAL_CAN_GetRxMessage(&hcan2, CAN_RX_FIFO1, &rx_header, data) == HAL_OK)
        {
            uint32_t id = (rx_header.IDE == CAN_ID_EXT) ? rx_header.ExtId : rx_header.StdId;
            process_btms_frame(id, rx_header.DLC, data);
        }
    }

    while (HAL_CAN_GetRxFifoFillLevel(&hcan2, CAN_RX_FIFO0) > 0)
    {
        if (HAL_CAN_GetRxMessage(&hcan2, CAN_RX_FIFO0, &rx_header, data) == HAL_OK)
        {
            uint32_t id = (rx_header.IDE == CAN_ID_EXT) ? rx_header.ExtId : rx_header.StdId;
            process_btms_frame(id, rx_header.DLC, data);
        }
    }
}



static void process_usb_command_line(const char *line)
{
    if (strcmp(line, "CTRL=AUTO") == 0)
    {
        btms_manual_control_enabled = 0;
        btms_manual_mode = 0;
        usb_command_count++;
        return;
    }

    const char prefix[] = "CTRL=MANUAL;MODE=";
    uint32_t prefix_len = sizeof(prefix) - 1;

    if (strncmp(line, prefix, prefix_len) == 0)
    {
        char mode_char = line[prefix_len];

        if (mode_char >= '0' && mode_char <= '3')
        {
            btms_manual_control_enabled = 1;
            btms_manual_mode = (uint8_t)(mode_char - '0');

            // Optioneel SET-veld uitlezen.
            // Ondersteunde commando's:
            // CTRL=MANUAL;MODE=1
            // CTRL=MANUAL;MODE=1;SET=25
            const char *set_ptr = strstr(line, ";SET=");
            if (set_ptr != NULL)
            {
                int set_value = 25;

                if (sscanf(set_ptr + 5, "%d", &set_value) == 1)
                {
                    btms_manual_set_temp_c = clamp_btms_set_temp((int16_t)set_value);
                }
                else
                {
                    usb_command_error_count++;
                    return;
                }
            }

            usb_command_count++;
            return;
        }
    }

    usb_command_error_count++;
}

extern "C" void BTMS_USB_Receive(uint8_t *buf, uint32_t len)
{
    static char rx_line[80];
    static uint32_t rx_index = 0;

    usb_rx_count++;

    for (uint32_t i = 0; i < len; i++)
    {
        char c = (char)buf[i];

        if (c == '\n' || c == '\r')
        {
            if (rx_index > 0)
            {
                rx_line[rx_index] = '\0';
                process_usb_command_line(rx_line);
                rx_index = 0;
            }
        }
        else
        {
            if (rx_index < (sizeof(rx_line) - 1))
            {
                rx_line[rx_index++] = c;
            }
            else
            {
                rx_index = 0;
                usb_command_error_count++;
            }
        }
    }
}


// ============================================================================
// Functies die vanuit cpp_link.cpp worden aangeroepen
// ============================================================================

static void usb_printf(const char *fmt, ...)
{
    char buffer[300];

    va_list args;
    va_start(args, fmt);
    int len = vsnprintf(buffer, sizeof(buffer) - 3, fmt, args);
    va_end(args);

    if (len <= 0)
    {
        usb_tx_error_count++;
        return;
    }

    if (len > 296)
    {
        len = 296;
    }

    buffer[len++] = '\r';
    buffer[len++] = '\n';
    buffer[len] = '\0';

    uint8_t result = CDC_Transmit_FS((uint8_t *)buffer, (uint16_t)len);

    if (result == 0)
    {
        usb_tx_count++;
        usb_last_tx_ms = HAL_GetTick();
    }
    else
    {
        usb_tx_error_count++;
    }
}

static void send_usb_status_line(void)
{
    usb_printf(
        "BMS_AVG=%d;"
        "BMS_MIN=%d;"
        "BMS_MAX=%d;"
        "PACK_MV=%lu;"
        "TX_MODE=%u;"
        "TX_SET=%d;"
        "TX_RELAY=%u;"
        "TX_VOLT=%u;"
        "RX_MODE=%u;"
        "RX_RELAY=%u;"
        "TOUT=%d;"
        "TIN=%d;"
        "TAMB=%d;"
        "PDEM_X10=%u;"
        "ERR=%u;"
        "ERRLVL=%u;"
        "BMS_RX=%lu;"
        "BTMS_RX=%lu;"
        "BTMS_TX=%lu;"
        "CTRL_AUTO=%u;"
        "MAN_MODE=%u;"
        "MAN_SET=%d;"
        "USB_RX=%lu;"
        "USB_CMD=%lu;"
        "USB_CMD_ERR=%lu",
        bms_avg_temp_c,
        bms_min_temp_c,
        bms_max_temp_c,
        bms_pack_mv,
        btms_command_mode,
        btms_command_set_temp_c,
        btms_command_relay,
        btms_command_pack_voltage_v,
        btms_mode,
        btms_relay_status,
        btms_tout_c,
        btms_tin_c,
        btms_tamb_c,
        btms_demand_power_x10_kw,
        btms_error_code,
        btms_error_level,
        can_rx_count,
        btms_rx_count,
        btms_tx_count,
        (uint8_t)(btms_manual_control_enabled ? 0 : 1),
        btms_manual_mode,
        btms_manual_set_temp_c,
        usb_rx_count,
        usb_command_count,
        usb_command_error_count
    );
}

void myCppProcessInit(void)
{
    HAL_Delay(500);
    can_start_all();
}

void myCppProcess(void)
{
    uint32_t last_bms_request_ms = 0;
    uint32_t last_btms_command_ms = 0;
    uint32_t last_usb_status_ms = 0;

    while (1)
    {
        uint32_t now = HAL_GetTick();

        if (now - last_bms_request_ms >= 500)
        {
            last_bms_request_ms = now;
            last_request_ms_debug = now;

            send_all_bms_requests();
        }

        if (now - last_btms_command_ms >= 1000)
        {
            last_btms_command_ms = now;

            send_btms_command();
        }

        read_can1_bms();
        read_can2_btms();

        if (now - last_usb_status_ms >= 500)
        {
            last_usb_status_ms = now;

            send_usb_status_line();
        }
    }
}
