import serial
import threading
import time

# ===== KONFIGURASI DI SINI =====
PORT = 'COM13'  # Ganti sesuai port kamu (COM17, /dev/ttyUSB0, dll)
BAUDRATE = 115200
SEND_DATA = bytes([0x99, 0xA5, 0x01])  # Data yang dikirim (HEX)
DELAY_MS = 5  # Delay kirim dalam ms
# ================================

class SimpleSerial:
    def __init__(self):
        self.ser = serial.Serial(PORT, BAUDRATE, timeout=0.1)
        self.running = True
        print(f"Connected to {PORT} at {BAUDRATE} baud\n")
        print("=" * 60)
        
    def receive_loop(self):
        """Loop untuk terima data"""
        while self.running:
            try:
                if self.ser.in_waiting > 0:
                    data = self.ser.read(self.ser.in_waiting)
                    hex_str = ' '.join([f'{b:02X}' for b in data])
                    ascii_str = ''.join([chr(b) if 32 <= b < 127 else '.' for b in data])
                    
                    print(f"\n[RX] HEX: {hex_str}")
                    print(f"[RX] ASCII: {ascii_str}")
                    print("-" * 60)
                    
                time.sleep(0.01)
            except Exception as e:
                print(f"RX Error: {e}")
                break
    
    def send_loop(self):
        """Loop untuk kirim data setiap 5ms"""
        counter = 0
        while self.running:
            try:
                self.ser.write(SEND_DATA)
                counter += 1
                hex_str = ' '.join([f'{b:02X}' for b in SEND_DATA])
                print(f"[TX #{counter}] Sent: {hex_str}", end='\r')
                time.sleep(DELAY_MS / 1000.0)
            except Exception as e:
                print(f"\nTX Error: {e}")
                break
    
    def run(self):
        """Jalankan kedua thread"""
        # Thread untuk receive
        rx_thread = threading.Thread(target=self.receive_loop, daemon=True)
        rx_thread.start()
        
        # Thread untuk send
        tx_thread = threading.Thread(target=self.send_loop, daemon=True)
        tx_thread.start()
        
        try:
            # Keep program running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nStopping...")
            self.running = False
            self.ser.close()

if __name__ == "__main__":
    try:
        terminal = SimpleSerial()
        terminal.run()
    except Exception as e:
        print(f"Error: {e}")
        print("\nPastikan:")
        print(f"1. Port {PORT} benar dan tersedia")
        print("2. Tidak ada aplikasi lain yang pakai port ini")
        print("3. Sudah install: pip install pyserial")