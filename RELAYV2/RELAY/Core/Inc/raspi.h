#ifndef RASPI_H
#define RASPY_H

#include <stdint.h>
#include "stm32f4xx_hal.h"

extern UART_HandleTypeDef huart1;
extern UART_HandleTypeDef huart2;
extern UART_HandleTypeDef huart3;
//extern uint8_t rx_byte;

void Tx_Raspy(void);
void Raspi_UART_Start(void);
void Rome_UART_Start(void);
void Nano_UART_Start(void);
void Send_ROME(uint8_t id_device,uint8_t data1,uint8_t data2);
void Send_RASPI(uint8_t id_device,uint8_t data1,uint8_t data2);
void Send_NANO(uint8_t id_device,uint8_t data1,uint8_t data2,uint8_t data3); // Modified Send_NANO declaration
//void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart);

// Reset UART state on init or reconnect
void Reset_UART_State(void); // Added this declaration

#endif
