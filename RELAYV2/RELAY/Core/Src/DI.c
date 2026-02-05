#include "DI.h"
#include "raspi.h"

// KONFIGURASI MODE & PIN
#define MODE_AUTO   1
#define MODE_BUTTON 0

// Pilih Mode Disini: MODE_AUTO atau MODE_BUTTON
#define CURRENT_MODE  MODE_AUTO

// Pilih Pin untuk Bit 0 (Data 01)
#define PIN_RASPY     GPIO_PIN_15

uint8_t Read_Discrete(void)
{
    uint8_t val = 0;

#if CURRENT_MODE == MODE_AUTO
    val = 0x01; // Simulasi: Paksa kirim 01 (PB15 dianggap aktif)
#else
    // Mode Button: Baca Pin Asli
    // Bit 0 sekarang membaca dari PIN_RASPY (PB15)
    val |= (HAL_GPIO_ReadPin(GPIOB, PIN_RASPY) == GPIO_PIN_SET) << 0;
    
    // Bit 1 tetap PB14
    val |= (HAL_GPIO_ReadPin(GPIOB, GPIO_PIN_14) == GPIO_PIN_SET) << 1;
    
    // Bit 2 sekarang baca PB13 (tukar posisi dengan PB15 yang lama)
    val |= (HAL_GPIO_ReadPin(GPIOB, GPIO_PIN_13) == GPIO_PIN_SET) << 2;
#endif

    return val;
}

void Value_Discrete(void){
	static uint32_t last_tx = 0;
	static uint32_t last_tx1 = 0;
	uint8_t val = Read_Discrete();
	uint8_t value_PB15;

	if(val & (1 << 0)){
	    // PB13 aktif
	}
	if(val & (1 << 1)){
		// PB14 aktif
	}
	// PB15 aktif
	if(val & (1 << 2))value_PB15 = 0x01;
	else value_PB15 = 0x00;

	if(HAL_GetTick() - last_tx >= 5)  // 5ms interval (200 Hz) - RESTORED
	{
	    last_tx = HAL_GetTick();
	    
	    // LED TOGGLE - Confirm function is running!
	    HAL_GPIO_TogglePin(GPIOC, GPIO_PIN_13);
	    
	    // Safe to use high frequency now (Non-blocking IT mode)
	    // FIX: Send actual 'val' instead of hardcoded 0x01
	    Send_RASPI(0x99,0xA5,val);
	}

	if(HAL_GetTick() - last_tx1 >= 300)
	{
		last_tx1 = HAL_GetTick();
		Send_NANO(0xAA,0x01,0x04,0xD2);
	}
}
