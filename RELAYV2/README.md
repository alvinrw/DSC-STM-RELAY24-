# DSC RELAY SYSTEM (STM32F407) - FINAL VERSION

**Language Selection / Pilih Bahasa:**
*   [English Documentation](#english-documentation)
*   [Dokumentasi Bahasa Indonesia](#dokumentasi-bahasa-indonesia)

---

# English Documentation

This project is a **Distributed Control System** connecting a **Raspberry Pi** (Main Brain) with field hardware (Relays & Analog Synchro Devices).

The STM32F407 (Folder `RELAYV2`) acts as the **MASTER CONTROLLER** which:
1.  Receives commands from the Raspberry Pi via UART.
2.  Directly controls **24 Relay Channels**.
3.  Forwards position data to the **DSC Converter (ROME Device)** via a separate UART.
4.  Reads **Digital Input (DI)** status and reports it back to the Raspberry Pi.

## Project Structure
There are 2 main folders/firmwares in this project:

### 1. `RELAYV2` (Master Controller)
*   **Function**: Main brain connected to the Raspberry Pi.
*   **Role**: Controls Relays and reads buttons (DI).
*   **Location**: `./RELAYV2`

### 2. `ROME_DSC1` (Slave / DSC Converter)
*   **Function**: Digital to Analog Synchro/Resolver Data Converter.
*   **Role**: Receives angle data from the STM32 Master, then drives aircraft indicator gauges.
*   **Location**: `./ROME_DSC1/ROME_DSC1`

## Key Features
*   **Bridge Communication**: Bridges the Raspberry Pi to multiple devices (Relays & Synchro) using a single USB port.
*   **Active High Relay Logic**: Software configured so User Input (1) = Relay ON, even though the actual hardware is Active Low.
*   **Robust Digital Input**: Uses a filtering mask system (only reads PB15) and internal Pull-Down resistors.
*   **Device ID Addressing**: Each DSC module has a unique ID that can be changed via code.

## Code Analysis & Logic Explanation

### 1. Digital Input Mode Configuration (`DI.c`)
This code configures how the STM32 reads the buttons.
```c
#include "DI.h"
#include "raspi.h"

// MODE CONFIGURATION
#define MODE_AUTO   1   // Simulation Mode: Sends '01' continuously without reading pins.
#define MODE_BUTTON 0   // Real Mode: Reads PB15 Pin status in real-time.

// SELECT MODE HERE: MODE_AUTO or MODE_BUTTON
#define CURRENT_MODE  MODE_BUTTON
```
*   **Explanation**: Currently set to `MODE_BUTTON` to match the physical state of pin PB15.

### 2. Active-High Relay Logic (`relay.c`)
This function inverts the hardware logic to be more intuitive for the programmer (1=ON).
```c
void Relay_Update(uint32_t relay_mask)
{
    // FIX: Invert Logic for Active High (1=ON, 0=OFF)
    // Since Relay Hardware is Active Low (0=ON), we invert logic:
    // Input 1 (ON)  -> Inverted (~) to 0 -> To Hardware -> Relay ON.
    // Input 0 (OFF) -> Inverted (~) to 1 -> To Hardware -> Relay OFF.
    relay_mask = ~relay_mask; 

    uint32_t pc_set, pc_reset;
    // ... etc ...
}
```
*   **Mechanism**: The tilde operator (`~`) inverts all bits. This software trick allows sending "1" to turn on Active Low relays.

## Guide to Changing Device IDs

For the DSC (Synchro) system, multiple devices with different IDs can exist. To change an ID, re-program the `ROME_DSC1` firmware.

**Steps to Change ID:**
1.  Open File: `ROME_DSC1/ROME_DSC1/Core/Src/main.c`
2.  Find the ID definition line (around line 36):
    ```c
    #define ID_DEVICE 05  <-- Change this number!
    ```
3.  **Change ID** as needed (e.g., 01, 02, 05, etc.).
    *   *Example*: Device 5 is special for EHSI (Direction Indicator) which has specific rotation logic.
4.  **Flash/Upload** the program to the respective Slave STM32 board.

**ID Mechanism**:
When STM32 Master sends data, it includes an ID in the packet (`0xBB, ID, Data, Data`). The Slave Firmware checks:
> *"Does the ID in the packet match my ID? If yes, I move. If no, I ignore."*

## Hardware Setup (Critical Wiring)

### Relay Master (`RELAYV2`)
*   **Digital Input (PB15)**: Must be connected to a Switch/Button.
    *   Uses *Internal Pull-Down*, so if the cable is disconnected it automatically reads 0 (OFF).

### Active Low Relay
*   Relay modules typically turn on when given **0V (GND)**.
*   Software handles this, so sending **1** from Raspberry Pi is sufficient to turn it ON.

---

# Dokumentasi Bahasa Indonesia

Project ini adalah **Sistem Kontrol Terdistribusi** yang menghubungkan **Raspberry Pi** (Main Brain) dengan perangkat keras lapangan (Relay & Analog Synchro Devices).

STM32F407 (Folder `RELAYV2`) bertindak sebagai **MASTER CONTROLLER** yang:
1.  Menerima perintah dari Raspberry Pi via UART.
2.  Mengontrol **24 Channel Relay** secara langsung.
3.  Meneruskan data posisi ke **DSC Converter (ROME Device)** via UART terpisah.
4.  Membaca status **Digital Input (DI)** dan melaporkannya kembali ke Raspberry Pi.

## Struktur Project
Terdapat 2 folder/firmware utama dalam project ini:

### 1. `RELAYV2` (Master Controller)
*   **Fungsi**: Otak utama yang terhubung ke Raspberry Pi.
*   **Tugas**: Menyalakan Relay dan membaca tombol (DI).
*   **Lokasi**: `./RELAYV2`

### 2. `ROME_DSC1` (Slave / DSC Converter)
*   **Fungsi**: Konverter data Digital ke Analog Synchro/Resolver.
*   **Tugas**: Menerima data sudut dari STM32 Master, lalu menggerakkan jarum indikator pesawat.
*   **Lokasi**: `./ROME_DSC1/ROME_DSC1`

## Fitur Utama
*   **Bridge Communication**: Menjembatani Raspberry Pi dengan banyak device (Relay & Synchro) hanya menggunakan 1 port USB.
*   **Active High Relay Logic**: Software dikonfigurasi agar input User (1) = Relay ON, meskipun hardware aslinya Active Low.
*   **Robust Digital Input**: Menggunakan sistem filtering mask (hanya baca PB15) dan Pull-Down resistor internal.
*   **Device ID Addressing**: Setiap modul DSC memiliki ID unik yang bisa diganti-ganti melalui coding.

## Bedah Kode & Penjelasan Logic

### 1. Konfigurasi Mode Digital Input (`DI.c`)
Coding ini mengatur bagaimana STM32 membaca tombol.
```c
#include "DI.h"
#include "raspi.h"

// KONFIGURASI MODE
#define MODE_AUTO   1   // Mode Simulasi: Kirim '01' terus menerus tanpa baca pin.
#define MODE_BUTTON 0   // Mode Asli: Baca status Pin PB15 secara real-time.

// PILIH MODE DISINI: MODE_AUTO atau MODE_BUTTON
#define CURRENT_MODE  MODE_BUTTON
```
*   **Penjelasan**: Saat ini diset ke `MODE_BUTTON` agar pembacaan sesuai kondisi fisik pin PB15.

### 2. Logic Relay Active-High (`relay.c`)
Fungsi ini membalik logika hardware supaya lebih intuitif bagi programmer (1=ON).
```c
void Relay_Update(uint32_t relay_mask)
{
    // FIX: Invert Logic untuk Active High (1=ON, 0=OFF)
    // Karena Hardware Relay Active Low (0=Nyala), maka kita balik logikanya:
    // Input 1 (ON)  -> Dibalik (~) jadi 0 -> Masuk Hardware -> Relay NYALA.
    // Input 0 (OFF) -> Dibalik (~) jadi 1 -> Masuk Hardware -> Relay MATI.
    relay_mask = ~relay_mask; 

    uint32_t pc_set, pc_reset;
    // ... dst ...
}
```
*   **Mekanisme**: Operator tilde (`~`) membalik semua bit (0 jadi 1, 1 jadi 0). Ini trik software agar kita bisa mengirim perintah "1" untuk menyalakan relay tipe Active Low.

## Panduan Mengganti ID Device

Untuk sistem DSC (Synchro), kita bisa memiliki banyak device dengan ID berbeda. Cara menggantinya adalah dengan memprogram ulang firmware `ROME_DSC1`.

**Langkah Ganti ID:**
1.  Buka File: `ROME_DSC1/ROME_DSC1/Core/Src/main.c`
2.  Cari baris definisi ID (sekitar baris 36):
    ```c
    #define ID_DEVICE 05  <-- Ganti angka ini!
    ```
3.  **Ganti ID** sesuai kebutuhan (Misal: 01, 02, 05, dll).
    *   *Contoh*: Device 5 khusus untuk EHSI (Indikator Arah) yang punya logika putaran khusus.
4.  **Flash/Upload** program ke board STM32 slave yang bersangkutan.

**Mekanisme ID**:
Saat STM32 Master mengirim data, dia menyertakan ID di dalam paketnya (`0xBB, ID, Data, Data`). Firmware Slave akan mengecek:
> *"Apakah ID di paket == ID saya? Kalau iya, saya gerak. Kalau tidak, saya abaikan."*

## Hardware Setup (Wiring Penting)

### Relay Master (`RELAYV2`)
*   **Digital Input (PB15)**: Wajib terhubung ke Switch/Tombol.
    *   Karena pakai *Internal Pull-Down*, kalau kabel lepas dia otomatis terbaca 0 (Mati).

### Active Low Relay
*   Modul relay umumnya menyala saat diberi tegangan **0V (GND)**.
*   Software sudah menangani ini, jadi dari Raspberry Pi cukup kirim **1** untuk Nyala.
