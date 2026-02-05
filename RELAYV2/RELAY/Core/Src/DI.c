#include "DI.h"
#include "raspi.h"

// KONFIGURASI MODE
#define MODE_AUTO   1   // Kirim 01 terus menerus (Simulasi)
#define MODE_BUTTON 0   // Baca Pin Asli (Manual)

// PILIH MODE DISINI: mode_auto	 dan mode_button
#define CURRENT_MODE  MODE_BUTTON

uint8_t Read_Discrete(void)
{
    uint8_t val = 0;

#if CURRENT_MODE == MODE_AUTO
    val = 0x01; // Simulasi: Paksa kirim 01 (Seolah-olah PB15 aktif)
#else
    // Mode Button: Logic disamakan dengan RELAY Masudin
    // Bit 0 = PB13
    val |= (HAL_GPIO_ReadPin(GPIOB, GPIO_PIN_13) == GPIO_PIN_SET) << 0;
    
    // Bit 1 = PB14
    val |= (HAL_GPIO_ReadPin(GPIOB, GPIO_PIN_14) == GPIO_PIN_SET) << 1;
    
    // Bit 2 = PB15 (Ini yang akan mentrigger pengiriman data 01)
    val |= (HAL_GPIO_ReadPin(GPIOB, GPIO_PIN_15) == GPIO_PIN_SET) << 2;
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
	if(val & (1 << 2))value_PB15 = 0x00;
	else value_PB15 = 0x01;

	if(HAL_GetTick() - last_tx >= 5)  // 5ms interval (200 Hz) - RESTORED
	{
	    last_tx = HAL_GetTick();
	    
	    // LED TOGGLE - Confirm function is running!
	    HAL_GPIO_TogglePin(GPIOC, GPIO_PIN_13);
	    
	    // Safe to use high frequency now (Non-blocking IT mode)
	    // FIX: Send value_PB15 (Like Masudin) instead of raw val
	    Send_RASPI(0x99,0xA5,value_PB15);
	}

	if(HAL_GetTick() - last_tx1 >= 300)
	{
		last_tx1 = HAL_GetTick();
		Send_NANO(0xAA,0x01,0x04,0xD2);
	}
}
