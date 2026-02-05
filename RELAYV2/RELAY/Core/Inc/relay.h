#ifndef RELAY_H
#define RELAY_H

#include "stm32f4xx_hal.h"

void Relay_GPIO_Init(void);
void Relay_Update(uint32_t relay_mask);
void Relay_On(uint8_t relay);
void Relay_Off(uint8_t relay);

#endif
