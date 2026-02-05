"""
RELAYV2 Complete Data Monitor - All-in-One
===========================================
Monitor SEMUA data dari Raspberry Pi → RELAYV2:
- Discrete A, B, C (decoded)
- ROME Device 1-5 (angles)
- Display interval bisa diatur

Port: COM yang terhubung ke RELAYV2 PA10 (RX) untuk sniff data
Baud: 115200

Author: Antigravity AI Assistant
Date: 2026-01-30
"""

import serial
import time
from datetime import datetime

# ===== CONFIGURATION =====
SERIAL_PORT = 'COM14'  # Port untuk sniff data Raspy → RELAYV2
BAUD_RATE = 115200
TIMEOUT = 1  # seconds
DISPLAY_INTERVAL = 10  # ⭐ Display every N seconds (UBAH DI SINI!)

# ===== STATISTICS =====
packet_count = 0
total_packets = 0

def print_header():
    """Print header information"""
    print("=" * 100)
    print("RELAYV2 Complete Data Monitor - All Data Display")
    print("=" * 100)
    print(f"Port: {SERIAL_PORT}")
    print(f"Baud Rate: {BAUD_RATE}")
    print(f"⭐ Display Interval: {DISPLAY_INTERVAL} seconds (edit DISPLAY_INTERVAL di line 20)")
    print("=" * 100)
    print("\nPress Ctrl+C to stop monitoring...\n")

def decode_mode(discrete_b):
    """Decode mode from Discrete B bits [1:0]"""
    mode_bits = discrete_b & 0x03
    modes = {0x00: "EADI", 0x01: "EHSI", 0x02: "RDU"}
    return modes.get(mode_bits, "Unknown")

def decode_nav_source(discrete_b):
    """Decode navigation source from Discrete B bits [3:2]"""
    nav_bits = (discrete_b >> 2) & 0x03
    sources = {0x00: "INS", 0x01: "TAC", 0x02: "VOR/ILS"}
    return sources.get(nav_bits, "Unknown")

def decode_country(discrete_c):
    """Decode country code from Discrete C bits [1:0]"""
    country_bits = discrete_c & 0x03
    countries = {0x00: "TNI_AU", 0x01: "Bangladesh", 0x02: "India", 0x03: "Pakistan"}
    return countries.get(country_bits, "Unknown")

def decode_gps_ins(discrete_c):
    """Decode GPS/INS from Discrete C bit 2"""
    return "GPS" if (discrete_c & (1 << 2)) == 0 else "INS"

def display_data(data):
    """Display complete data in organized format"""
    timestamp = data['timestamp']
    
    print("\n" + "=" * 100)
    print(f"📊 DATA SNAPSHOT @ {timestamp}")
    print("=" * 100)
    
    # Discrete Data
    print(f"\n🔢 DISCRETE DATA:")
    print(f"   Mode:         {data['mode']}")
    print(f"   Nav Source:   {data['nav_source']}")
    print(f"   Country:      {data['country']}")
    print(f"   GPS/INS:      {data['gps_ins']}")
    print(f"   Discrete A:   0x{data['discrete_a']:02X} (binary: {data['discrete_a']:08b})")
    print(f"   Discrete B:   0x{data['discrete_b']:02X} (binary: {data['discrete_b']:08b})")
    print(f"   Discrete C:   0x{data['discrete_c']:02X} (binary: {data['discrete_c']:08b})")
    
    # ROME Devices
    print(f"\n🎯 ROME DEVICES (Angles):")
    for i in range(5):
        dev_id = i + 1
        raw_value = data[f'rome_{dev_id}_raw']
        angle = data[f'rome_{dev_id}_angle']
        print(f"   Device {dev_id}:    {raw_value:5d} = {angle:7.1f}°")
    
    # Statistics
    print(f"\n📈 STATISTICS:")
    print(f"   Total Packets:     {total_packets:,}")
    print(f"   Packets/sec:       {data['rate']:.1f} Hz")
    print(f"   Next update in:    {DISPLAY_INTERVAL} seconds")
    print("=" * 100)

def main():
    global packet_count, total_packets
    
    print_header()
    
    try:
        # Open serial port
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT)
        print(f"✅ Connected to {SERIAL_PORT} at {BAUD_RATE} baud\n")
        print("Waiting for data...\n")
        
        # Flush input buffer
        ser.reset_input_buffer()
        
        buffer = bytearray()
        last_display_time = time.time()
        last_count_time = time.time()
        last_packet_count = 0
        latest_data = None
        
        while True:
            # Read available data
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                buffer.extend(data)
                
                # Look for packet header (A5 99)
                while len(buffer) >= 15:
                    # Find header
                    header_idx = -1
                    for i in range(len(buffer) - 1):
                        if buffer[i] == 0xA5 and buffer[i+1] == 0x99:
                            header_idx = i
                            break
                    
                    if header_idx == -1:
                        # No header found, keep last byte
                        buffer = buffer[-1:]
                        break
                    
                    # Remove data before header
                    if header_idx > 0:
                        buffer = buffer[header_idx:]
                    
                    # Check if we have full packet (15 bytes)
                    if len(buffer) >= 15:
                        packet = buffer[:15]
                        buffer = buffer[15:]
                        
                        # Parse packet: [A5 99 | DA DB DC | D1_MSB D1_LSB D2_MSB D2_LSB ... D5_MSB D5_LSB]
                        discrete_a = packet[2]
                        discrete_b = packet[3]
                        discrete_c = packet[4]
                        
                        # Parse ROME devices (5 devices, 2 bytes each)
                        rome_data = {}
                        for i in range(5):
                            dev_id = i + 1
                            msb = packet[5 + (i * 2)]
                            lsb = packet[6 + (i * 2)]
                            raw_value = (msb << 8) | lsb
                            
                            # CORRECT FORMULA: Convert raw (0-65535) to degrees (0-360)
                            angle = (raw_value * 360.0) / 65535.0
                            
                            rome_data[f'rome_{dev_id}_raw'] = raw_value
                            rome_data[f'rome_{dev_id}_angle'] = angle
                        
                        # Calculate rate
                        current_time = time.time()
                        time_diff = current_time - last_count_time
                        if time_diff >= 1.0:
                            rate = (total_packets - last_packet_count) / time_diff
                            last_packet_count = total_packets
                            last_count_time = current_time
                        else:
                            rate = 0
                        
                        # Store latest data
                        latest_data = {
                            'timestamp': datetime.now().strftime("%H:%M:%S.%f")[:-3],
                            'mode': decode_mode(discrete_b),
                            'nav_source': decode_nav_source(discrete_b),
                            'country': decode_country(discrete_c),
                            'gps_ins': decode_gps_ins(discrete_c),
                            'discrete_a': discrete_a,
                            'discrete_b': discrete_b,
                            'discrete_c': discrete_c,
                            'rate': rate,
                            **rome_data
                        }
                        
                        total_packets += 1
                        
                        # Display every N seconds
                        if current_time - last_display_time >= DISPLAY_INTERVAL:
                            if latest_data:
                                display_data(latest_data)
                                last_display_time = current_time
                    else:
                        break
            
            # Small delay to prevent CPU hogging
            time.sleep(0.001)
    
    except serial.SerialException as e:
        print(f"\n❌ Serial Error: {e}")
        print(f"\nTroubleshooting:")
        print(f"  1. Check if port {SERIAL_PORT} is correct")
        print(f"  2. Check if port is not used by another program")
        print(f"  3. Try different COM port number")
        return
    
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Monitoring stopped by user")
        print(f"\n📊 Final Statistics:")
        print(f"   Total packets decoded: {total_packets:,}")
    
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print(f"\n✅ Serial port {SERIAL_PORT} closed")

if __name__ == "__main__":
    main()
