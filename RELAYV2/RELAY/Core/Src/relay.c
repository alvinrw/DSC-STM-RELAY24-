#include "relay.h"

uint32_t relay_state = 0;

void Relay_GPIO_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStruct = {0};

    __HAL_RCC_GPIOC_CLK_ENABLE();
    __HAL_RCC_GPIOD_CLK_ENABLE();
    __HAL_RCC_GPIOA_CLK_ENABLE();

    /* ===== PC0–PC15 (Relay 0–15) ===== */
    GPIO_InitStruct.Pin = 0xFFFF;
    GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);

    /* ===== PD0–PD3 (Relay 16–19) ===== */
    GPIO_InitStruct.Pin = GPIO_PIN_0 | GPIO_PIN_1 |
                          GPIO_PIN_2 | GPIO_PIN_3;
    HAL_GPIO_Init(GPIOD, &GPIO_InitStruct);

    /* ===== PA4–PA7 (Relay 20–23) ===== */
	GPIO_InitStruct.Pin = GPIO_PIN_4 | GPIO_PIN_5 |
						  GPIO_PIN_6 | GPIO_PIN_7;
	HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);
}

void Relay_Update(uint32_t relay_mask)
{
    uint32_t pc_set, pc_reset;
    uint32_t pd_set, pd_reset;
    uint32_t pa_set, pa_reset;

    /* ===== PC0–PC15 (Relay 1–16) ===== */
    pc_set   = relay_mask & 0x0000FFFF;
    pc_reset = (~relay_mask) & 0x0000FFFF;
    GPIOC->BSRR = (pc_reset << 16) | pc_set;

    /* ===== PD0–PD3 (Relay 17–20) ===== */
    pd_set   = (relay_mask >> 16) & 0x000F;
    pd_reset = (~relay_mask >> 16) & 0x000F;
    GPIOD->BSRR = (pd_reset << 16) | pd_set;

    /* ===== PA4–PA7 (Relay 20–23) ===== */
	pa_set   = (relay_mask >> 20) & 0x000F;
	pa_reset = (~relay_mask >> 20) & 0x000F;
	GPIOA->BSRR = (pa_reset << (16 + 4)) | (pa_set << 4);
}

void Relay_Off(uint8_t relay)
{
    relay_state |= (1UL << (relay - 1));
    Relay_Update(relay_state);
}

void Relay_On(uint8_t relay)
{
    relay_state &= ~(1UL << (relay - 1));
    Relay_Update(relay_state);
}


void Relay_Test_All(void)
{
    uint32_t relay_mask = 0;
    for (int i = 0; i < 24; i++)
    {
        relay_mask |= (1UL << i);
        Relay_Update(relay_mask);
        HAL_Delay(300);
    }

    HAL_Delay(1000);

    relay_mask = 0;
    Relay_Update(relay_mask);
}
