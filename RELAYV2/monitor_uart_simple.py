import serial
import time
import sys

# Konfigurasi COM PORT
COM_PORT = 'COM13'
BAUD_RATE = 115200

def monitor_uart():
    print(f"Membuka {COM_PORT} dengan baudrate {BAUD_RATE}...")
    try:
        ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=0.1)
        print("Berhasil terhubung! Tekan Ctrl+C untuk berhenti.")
        print("-" * 50)
        
        while True:
            # Baca data yang tersedia
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                
                # Format ke HEX string (contoh: 99 A5 01)
                hex_string = ' '.join(f'{b:02X}' for b in data)
                
                # Print Hex dan ASCII (kalau ada text terselip)
                timestamp = time.strftime("[%H:%M:%S]")
                print(f"{timestamp} RAW HEX: {hex_string}")
                
            time.sleep(0.01) # Istirahat dikit biar CPU gak panas

    except serial.SerialException as e:
        print(f"Error membuka port {COM_PORT}: {e}")
        print("Pastikan port tidak sedang dipakai aplikasi lain (seperti Serial Monitor IDE).")
    except KeyboardInterrupt:
        print("\nMonitoring dihentikan.")
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("Port ditutup.")

if __name__ == "__main__":
    monitor_uart()
