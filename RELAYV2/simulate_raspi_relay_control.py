import serial
import time
import struct

# KONFIGURASI
COM_PORT = 'COM13'
BAUD_RATE = 115200

def create_packet(relay_a, relay_b, relay_c):
    # Header
    packet = bytearray([0xA5, 0x99])
    
    # Payload Byte 0-2 (Relay/Discrete A, B, C)
    packet.append(relay_a)
    packet.append(relay_b)
    packet.append(relay_c)
    
    # Payload Byte 3-12 (Sisanya 10 byte dummy/data lain, isi 0 aja)
    for _ in range(10):
        packet.append(0x00)
        
    return packet

def main():
    print(f"Membuka {COM_PORT}...")
    try:
        ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
        print("Berhasil! Program Simulasi Raspberry Pi.")
        print("Ketik '1' lalu Enter: Nyalakan Relay Ganjil (1, 3, 5...)")
        print("Ketik '0' lalu Enter: Matikan Semua Relay")
        print("Ketik 'q' untuk keluar.")
        print("-" * 50)

        while True:
            cmd = input("Masukkan Perintah (1/0): ").strip().lower()
            
            if cmd == 'q':
                break
            
            elif cmd == '1':
                # Relay Ganjil (Bit 0, 2, 4, 6) -> Binary 01010101 -> Hex 0x55
                # Kita set untuk Discrete A, B, dan C
                packet = create_packet(0x55, 0x55, 0x55)
                ser.write(packet)
                print(f"[SENT] Relay Ganjil ON! Data: {packet.hex().upper()}")
                
            elif cmd == '0':
                # Semua Relay Mati -> 0x00
                packet = create_packet(0x00, 0x00, 0x00)
                ser.write(packet)
                print(f"[SENT] Semua Relay OFF! Data: {packet.hex().upper()}")
                
            else:
                print("Perintah tidak dikenal. Ketik 1 atau 0.")

    except serial.SerialException as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        print("\nKeluar.")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()

if __name__ == "__main__":
    main()
