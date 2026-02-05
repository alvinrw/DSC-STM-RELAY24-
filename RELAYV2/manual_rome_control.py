"""
RELAY SIMULATOR (MANUAL ROME CONTROL)
=====================================
Script ini mensimulasikan peran RELAY untuk mengirim data langsung
ke ROME_DSC1 via USB-TTL Converter.

Fitur:
- Bisa pilih Device ID (Target)
- Bisa input Sudut (0-360)
- Otomatis handle encoding khusus Device 5 (EHSI Relative)

Protocol Output: [0xBB, ID, MSB, LSB]

Author: Antigravity AI Assistant
Date: 2026-02-02
"""

import serial
import time
import sys

# ===== KONFIGURASI =====
SERIAL_PORT = 'COM14'   # Ganti dengan Port USB-TTL kamu
BAUD_RATE = 115200
DEFAULT_DEVICE_ID = 2   # Target Device ID Default

def get_valid_float(prompt):
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("❌ Input tidak valid. Masukkan angka.")

def calculate_raw_data(device_id, angle):
    """
    Hitung Raw Data 16-bit berdasarkan Dev ID & Sudut.
    """
    if device_id == 5:
        # === LOGIKA KHUSUS DEVICE 5 (EHSI) ===
        # Encoding: (Angle + 179.9) * 10
        # Range Angle: -180.0 s/d +180.0 (biasanya relative course)
        
        encoded_val = (angle + 179.9) * 10
        
        # Clamp limit agar tidak overflow uint16 jika user input aneh-aneh
        # Tapi technically Device 5 support negative values via int16 casting di firmware
        # Kita kirim sebagai unsigned 16-bit representation
        
        int_val = int(encoded_val)
        
        # Handle negative logic for python bitwise
        if int_val < 0:
            int_val = int_val & 0xFFFF  # Convert -1 to 0xFFFF
            
        return int_val
    
    else:
        # === LOGIKA STANDAR (Device 1, 2, 3, 4) ===
        # Encoding: Angle * 10
        return int(angle * 10)

def main():
    print("="*60)
    print("      MANUAL ROME CONTROL (SIMULATOR)      ")
    print("="*60)
    
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"✅ Connected to {SERIAL_PORT}")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        return

    try:
        while True:
            print("\n" + "="*40)
            # 1. Pilih Device (Sekali di awal loop luar)
            try:
                prompt_dev = f"Target Device ID (1-5) [Enter={DEFAULT_DEVICE_ID}, q=quit]: "
                dev_input = input(prompt_dev)
                
                if dev_input.lower() == 'q': break
                
                if dev_input.strip() == "":
                    device_id = DEFAULT_DEVICE_ID
                else:
                    device_id = int(dev_input)
            except:
                print("❌ Invalid Device ID")
                continue

            # 2. Loop Input Sudut (Continuous)
            print(f"✅ Mode: Mengendalikan Device {device_id}")
            print("   Available Commands:")
            print("   [Number] : Set Angle (e.g. 120.5)")
            print("   'a'      : Auto Rotate (Animation)")
            print("   'c'      : CALIBRATION MODE (Cari Offset)")
            print("   'b'      : Back to Device Select")
            print("   'q'      : Quit App")
            print("-" * 40)

            while True:
                user_val = input(f"Sudut Dev {device_id} > ")
                
                # === COMMAND: CALIBRATION MODE ===
                if user_val.lower() == 'c':
                    print("\n🔧 --- CALIBRATION MODE ---")
                    print("1. Putar jarum sampai menunjuk angka 0 (Zero Physical Position).")
                    print("2. Gunakan: 'w/s' (+/- 10), 'd/a' (+/- 1), 'e/q' (+/- 0.1)")
                    print("3. Tekan ENTER jika jarum sudah pas di 0.")
                    
                    calib_angle = 0.0
                    while True:
                        # Kirim Data
                        raw_data = calculate_raw_data(device_id, calib_angle)
                        msb = (raw_data >> 8) & 0xFF
                        lsb = raw_data & 0xFF
                        ser.write(bytearray([0xBB, device_id, msb, lsb]))
                        
                        print(f"\r🎯 Calib Angle: {calib_angle:.1f}° | Raw Sent: {raw_data} (0x{raw_data:04X})  ", end="")
                        
                        # Input Kontrol
                        key = input() # Tunggu enter
                        if key == "": break # DONE
                        
                        if key == 'w': calib_angle += 10.0
                        elif key == 's': calib_angle -= 10.0
                        elif key == 'd': calib_angle += 1.0
                        elif key == 'a': calib_angle -= 1.0
                        elif key == 'e': calib_angle += 0.1
                        elif key == 'q': calib_angle -= 0.1
                        
                        # Wrap around
                        if calib_angle >= 360.0: calib_angle -= 360.0
                        if calib_angle < 0.0: calib_angle += 360.0
                    
                    print(f"\n\n✅ CALIBRATION DONE!")
                    print(f"Saat ini Raw Data = 0x{raw_data:04X}")
                    
                    # Hitung Offset
                    # Logika: Jika kita kirim X supaya jarum jadi 0.
                    # Maka Offset yang harus diset di firmware adalah (65536 - X).
                    # Supaya nanti kalau firmware dapet data 0, dia nambahin Offset ini dan outputnya jadi X.
                    
                    offset_needed = (65536 - raw_data) & 0xFFFF
                    print("-" * 40)
                    print(f"📣 COPY KODE INI KE main.c:")
                    print(f"#define DSC_ZERO_OFFSET   0x{offset_needed:04X}")
                    print("-" * 40)
                    print("Setelah update main.c, re-upload codingnya.\n")
                    continue

                # === COMMAND: AUTO ROTATE ===
                if user_val.lower() == 'a':
                    print("\n🔄 --- AUTO ROTATE MODE ---")
                    try:
                        inc_str = input("Masukkan Increment (Default 5.0) : ")
                        step = float(inc_str) if inc_str.strip() else 5.0
                        
                        dly_str = input("Masukkan Delay detik (Default 0.05) : ")
                        delay = float(dly_str) if dly_str.strip() else 0.05
                        
                        print(f"🚀 Muter mode ON! (Step: {step}, Delay: {delay}s)")
                        print("⏹️  Tekan CTRL+C untuk stop dan kembali ke menu.\n")
                        
                        curr_angle = 0.0
                        while True:
                            # 1. Hitung & Kirim
                            raw_data = calculate_raw_data(device_id, curr_angle)
                            msb = (raw_data >> 8) & 0xFF
                            lsb = raw_data & 0xFF
                            packet = bytearray([0xBB, device_id, msb, lsb])
                            ser.write(packet)
                            
                            # 2. Print Status (Overwrite line for clean look via \r, or simple print)
                            # print(f"\r⏳ Sudut: {curr_angle:>6.1f}° | Raw: {raw_data:>5}", end="", flush=True)
                            print(f"⏳ Auto: {curr_angle:.1f}° -> Raw: {raw_data}")

                            # 3. Increment
                            curr_angle += step
                            if curr_angle >= 360.0:
                                curr_angle -= 360.0
                            
                            time.sleep(delay)

                    except KeyboardInterrupt:
                        print("\n\n⏹️  Auto Rotate Stopped. Kembali ke manual.")
                        continue # Back to inner loop
                    except ValueError:
                        print("❌ Input tidak valid.")
                        continue

                # === COMMAND: BACK / QUIT ===
                if user_val.lower() == 'b': break # Back to device selection
                if user_val.lower() == 'q': 
                    ser.close()
                    sys.exit()

                # === MANUAL INPUT ===
                try:
                    target_angle = float(user_val)
                except ValueError:
                    # If not a command and not a number, skip
                    if user_val.strip() != "":
                        print("❌ Masukkan angka atau command 'a'/'b'/'c'/'q'")
                    continue
                
                # 3. Hitung Raw Data
                raw_data = calculate_raw_data(device_id, target_angle)
                
                # Pecah ke MSB LSB
                msb = (raw_data >> 8) & 0xFF
                lsb = raw_data & 0xFF
                
                # 4. Kirim Paket: 0xBB, ID, MSB, LSB
                packet = bytearray([0xBB, device_id, msb, lsb])
                ser.write(packet)
                
                print(f"   📤 SENT: [BB {device_id:02X} {msb:02X} {lsb:02X}] -> Raw: {raw_data} (Angle: {target_angle})")

    except KeyboardInterrupt:
        print("\nSee ya!")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()

if __name__ == "__main__":
    main()
