#include "raspi.h"
#include "relay.h"
#include <string.h>
#include <stdio.h>

#define RX_BUF_SIZE 256  // Ring Buffer Size
#define TIMEOUT_THRESHOLD 50000

// === RING BUFFER ===
volatile uint8_t rx_buffer[RX_BUF_SIZE];
volatile uint16_t rx_head = 0;
volatile uint16_t rx_tail = 0;
uint8_t rx_temp_byte; // Temporary buffer for 1-byte reception

uint8_t payload[16];

// State variables
uint8_t discreate_A[8];
uint8_t discreate_B[8];
uint8_t discreate_C[8];

char* country_code;
char* navigation_source;

// TX queue for ROME
typedef struct {
    uint8_t data[4];
} ROME_Packet;

#define ROME_QUEUE_SIZE 16
ROME_Packet rome_tx_queue[ROME_QUEUE_SIZE];
volatile uint8_t rome_queue_head = 0;
volatile uint8_t rome_queue_tail = 0;
volatile uint8_t rome_tx_busy = 0;

extern UART_HandleTypeDef huart1;
extern UART_HandleTypeDef huart2;
extern UART_HandleTypeDef huart3;

// ============================================================================
// INITIALIZATION
// ============================================================================

void Reset_UART_State(void){
    rx_head = 0;
    rx_tail = 0;
    rome_queue_head = 0;
    rome_queue_tail = 0;
    rome_tx_busy = 0;
    
    // Clear overflow errors
    __HAL_UART_CLEAR_OREFLAG(&huart1);
}

void Raspi_UART_Start(void)
{
    Reset_UART_State();
    
    // Start Interrupt Reception (1 byte at a time)
    HAL_UART_Receive_IT(&huart1, &rx_temp_byte, 1);
}

void Rome_UART_Start(void)
{
    rome_tx_busy = 0;
}

void Nano_UART_Start(void)
{
    // Ready
}

// ============================================================================
// TRANSMIT FUNCTIONS
// ============================================================================

void Send_NANO(uint8_t header, uint8_t ID, uint8_t data, uint8_t data1){
    static uint8_t send_nano[4]; // STATIC to persist for IT
    send_nano[0] = header;
    send_nano[1] = ID;
    send_nano[2] = data;
    send_nano[3] = data1;
    HAL_UART_Transmit_IT(&huart3, send_nano, 4);
}

// Queue for ROME (Buffer packets to avoid blocking)
void Queue_ROME(uint8_t id_device, uint8_t data1, uint8_t data2){
    uint8_t next_head = (rome_queue_head + 1) % ROME_QUEUE_SIZE;

    // If buffer full, do nothing (drop packet to prevent overflow)
    if(next_head == rome_queue_tail){
        return;
    }

    rome_tx_queue[rome_queue_head].data[0] = 0xBB;
    rome_tx_queue[rome_queue_head].data[1] = id_device;
    rome_tx_queue[rome_queue_head].data[2] = data1;
    rome_tx_queue[rome_queue_head].data[3] = data2;

    rome_queue_head = next_head;
}

// Process ROME TX Queue (Call from Main Loop)
void Process_ROME_Queue(void){
    if(rome_tx_busy) return;

    if(rome_queue_tail != rome_queue_head){
        rome_tx_busy = 1;
        HAL_UART_Transmit_IT(&huart2, rome_tx_queue[rome_queue_tail].data, 4);
    }
}

// TX Complete Callback
void HAL_UART_TxCpltCallback(UART_HandleTypeDef *huart){
    if(huart->Instance == USART2){
        // ROME TX Done, advance tail
        rome_queue_tail = (rome_queue_tail + 1) % ROME_QUEUE_SIZE;
        rome_tx_busy = 0;
    }
}

void Send_RASPI(uint8_t id_device, uint8_t data1, uint8_t data2){
    static uint8_t send_raspi[3]; // STATIC to persist for IT
    send_raspi[0] = id_device;
    send_raspi[1] = data1;
    send_raspi[2] = data2;
    HAL_UART_Transmit_IT(&huart1, send_raspi, 3);
}

// ============================================================================
// RX INTERRUPT CALLBACK (High Priority)
// ============================================================================

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart){
    if(huart->Instance == USART1){
        // 1. Put received byte into Ring Buffer
        uint16_t next_head = (rx_head + 1) % RX_BUF_SIZE;
        if(next_head != rx_tail){
            rx_buffer[rx_head] = rx_temp_byte;
            rx_head = next_head;
        }
        // else: Buffer Full! Drop byte (Overrun software protection)

        // 2. Restart Reception immediately
        HAL_UART_Receive_IT(&huart1, &rx_temp_byte, 1);
    }
}

void HAL_UART_ErrorCallback(UART_HandleTypeDef *huart){
    if(huart->Instance == USART1){
        // Clear HW Errors
        __HAL_UART_CLEAR_OREFLAG(huart);
        __HAL_UART_CLEAR_NEFLAG(huart);
        __HAL_UART_CLEAR_FEFLAG(huart);
        
        // Restart Reception
        HAL_UART_Receive_IT(&huart1, &rx_temp_byte, 1);
    }
}

// ============================================================================
// PACKET PROCESSING (Main Loop)
// ============================================================================

void Parse_Status_Packet(uint8_t* data){
    // Protocol: [0x99 0xA5 value]
    // Value = Relay Mask (8-bit for first 8 relays)
    uint8_t relay_val = data[2];
    
    // Convert 8-bit to 32-bit mask for Relay_Update
    uint32_t current_mask = relay_val; // Maps to Relay 1-8 (PC0-PC7)
    
    // Update Relay Hardware
    Relay_Update(current_mask);
}

void Parse_Data_Packet(uint8_t* data){
    // [0xA5 0x99 + 13 bytes]
    memcpy(payload, &data[2], 13);
    
    // === AUTOMATIC RELAY MAPPING ===
    // Discrete A (payload[0]) -> Relay 1-8
    // Discrete B (payload[1]) -> Relay 9-16
    // Discrete C (payload[2]) -> Relay 17-24
    
    uint32_t relay_mask = 0;
    relay_mask |= (uint32_t)payload[0];         // Byte 0 -> Bit 0-7
    relay_mask |= (uint32_t)payload[1] << 8;    // Byte 1 -> Bit 8-15
    relay_mask |= (uint32_t)payload[2] << 16;   // Byte 2 -> Bit 16-23
    
    Relay_Update(relay_mask);
    
    // Queue to ROME (Non-blocking!)
    for(int i = 0; i < 5; i++){
        Queue_ROME(i + 1, payload[3 + (i * 2)], payload[4 + (i * 2)]);
    }
}

// State Machine for Packet Parsing
void Process_RX_Buffer(void){
    static uint8_t pkt_buf[20];
    static uint8_t pkt_idx = 0;
    
    // Process all available bytes in Ring Buffer
    while(rx_tail != rx_head){
        uint8_t byte = rx_buffer[rx_tail];
        rx_tail = (rx_tail + 1) % RX_BUF_SIZE;
        
        // Add to temp packet buffer
        if(pkt_idx < sizeof(pkt_buf)){
            pkt_buf[pkt_idx++] = byte;
        }
        
        // Check Packet
        if(pkt_idx >= 3){
            // Check STATUS [99 A5 val]
            if(pkt_buf[0] == 0x99 && pkt_buf[1] == 0xA5){
                Parse_Status_Packet(pkt_buf);
                pkt_idx = 0;
                continue;
            }
        }
        
        if(pkt_idx >= 15){
            // Check DATA [A5 99 ... 13 bytes]
            if(pkt_buf[0] == 0xA5 && pkt_buf[1] == 0x99){
                Parse_Data_Packet(pkt_buf);
                pkt_idx = 0;
                continue;
            }
        }
        
        // Garbage Collection / Sliding Window
        if(pkt_idx >= 20){
            // Shift left
             uint8_t found = 0;
            for(uint8_t i = 1; i < pkt_idx - 1; i++){
                if((pkt_buf[i] == 0x99 && pkt_buf[i+1] == 0xA5) ||
                   (pkt_buf[i] == 0xA5 && pkt_buf[i+1] == 0x99)){
                    memmove(pkt_buf, &pkt_buf[i], pkt_idx - i);
                    pkt_idx -= i;
                    found = 1;
                    break;
                }
            }
            if(!found) pkt_idx = 0;
        }
    }
}

// ============================================================================
// MAIN LOOP FUNCTION
// ============================================================================

void Tx_Raspy(void){
    // 1. Process received data from Ring Buffer
    Process_RX_Buffer();
    
    // 2. Process ROME TX Queue
    Process_ROME_Queue();
}
