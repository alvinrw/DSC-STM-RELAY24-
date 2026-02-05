"""
RELAYV2 Discrete Monitor - Enhanced Version
============================================
Script untuk monitor dan decode Discrete A, B, C dari data Raspberry Pi
dengan detail bit mapping untuk setiap mode (EADI, EHSI, RDU)

Port: COM yang terhubung ke RELAYV2 PA10 (RX) untuk sniff data
Baud: 115200
"""

import serial
import time
from datetime import datetime

# ===== CONFIGURATION =====
SERIAL_PORT = 'COM14'  # Port untuk sniff data Raspy -> RELAYV2
BAUD_RATE = 115200
TIMEOUT = 1  # seconds
DISPLAY_INTERVAL = 5  # Display every N seconds (ubah sesuai kebutuhan!)

# ===== STATISTICS =====
packet_count = 0

def print_header():
    """Print header information"""
    print("=" * 120)
    print("RELAYV2 Discrete Monitor - Enhanced with Bit Mapping")
    print("=" * 120)
    print(f"Port: {SERIAL_PORT}")
    print(f"Baud Rate: {BAUD_RATE}")
    print(f"Display Interval: {DISPLAY_INTERVAL} seconds")
    print("=" * 120)
    print("\nPress Ctrl+C to stop monitoring...\n")

def decode_discrete_a_eadi(discrete_a):
    """Decode Discrete A for EADI mode"""
    flags = []
    if discrete_a & (1 << 0): flags.append("GS_Valid")
    if discrete_a & (1 << 1): flags.append("Gyro_Mon")
    if discrete_a & (1 << 2): flags.append("FD_Valid")
    if discrete_a & (1 << 3): flags.append("ROT_Valid")
    if discrete_a & (1 << 4): flags.append("NVIS_Sel")
    if discrete_a & (1 << 5): flags.append("DH_Input")
    return flags if flags else ['None']

def decode_discrete_a_ehsi(discrete_a):
    """Decode Discrete A for EHSI mode"""
    flags = []
    if discrete_a & (1 << 0): flags.append("GS_Valid")
    if discrete_a & (1 << 1): flags.append("TRUE/MAG")
    if discrete_a & (1 << 2): flags.append("FMS_Decimal")
    if discrete_a & (1 << 3): flags.append("WP_Alert")
    if discrete_a & (1 << 4): flags.append("NVIS_Sel")
    return flags if flags else ['None']

def decode_discrete_a_rdu(discrete_a):
    """Decode Discrete A for RDU mode"""
    flags = []
    if discrete_a & (1 << 4): flags.append("NVIS_Sel")
    if discrete_a & (1 << 6): flags.append("Video_Radar_ON")
    return flags if flags else ['None']

def decode_discrete_b_eadi(discrete_b):
    """Decode Discrete B for EADI mode"""
    flags = []
    if discrete_b & (1 << 4): flags.append("Auto_Test")
    if discrete_b & (1 << 5): flags.append("LAT/BAR_View")
    if discrete_b & (1 << 6): flags.append("ILS_Freq_Tuned")
    if discrete_b & (1 << 7): flags.append("NAV_Super_Flag")
    return flags if flags else ['None']

def decode_discrete_b_ehsi(discrete_b):
    """Decode Discrete B for EHSI mode"""
    flags = []
    if discrete_b & (1 << 4): flags.append("Auto_Test")
    if discrete_b & (1 << 5): flags.append("Heading_Mon")
    if discrete_b & (1 << 6): flags.append("ILS_Freq_Tuned")
    if discrete_b & (1 << 7): flags.append("NAV_Valid")
    return flags if flags else ['None']

def decode_discrete_b_rdu(discrete_b):
    """Decode Discrete B for RDU mode"""
    return ['None']  # No specific flags for RDU

def decode_discrete_c_eadi(discrete_c):
    """Decode Discrete C for EADI mode"""
    flags = []
    if discrete_c & (1 << 2): flags.append("Radio_Alt_Mon")
    if discrete_c & (1 << 3): flags.append("REV_Mode")
    if discrete_c & (1 << 4): flags.append("Inner_Marker")
    if discrete_c & (1 << 5): flags.append("Outer_Marker")
    if discrete_c & (1 << 6): flags.append("Middle_Marker")
    return flags if flags else ['None']

def decode_discrete_c_ehsi(discrete_c):
    """Decode Discrete C for EHSI mode"""
    flags = []
    if discrete_c & (1 << 3): flags.append("Back_Loc_Sense")
    if discrete_c & (1 << 5): flags.append("VHF_NAV_Config")
    return flags if flags else ['None']

def decode_discrete_c_rdu(discrete_c):
    """Decode Discrete C for RDU mode"""
    return ['None']  # No specific flags for RDU

def decode_mode(discrete_b):
    """Decode mode from Discrete B bits [1:0]"""
    mode_bits = discrete_b & 0x03
    if mode_bits == 0x00:
        return "EADI"
    elif mode_bits == 0x01:
        return "EHSI"
    elif mode_bits == 0x02:
        return "RDU"
    else:
        return "Unknown"

def decode_nav_source(discrete_b):
    """Decode navigation source from Discrete B bits [3:2]"""
    nav_bits = (discrete_b >> 2) & 0x03
    if nav_bits == 0x00:
        return "INS"
    elif nav_bits == 0x01:
        return "TAC"
    elif nav_bits == 0x02:
        return "VOR/ILS"
    else:
        return "Unknown"

def decode_country(discrete_c):
    """Decode country code from Discrete C bits [1:0]"""
    country_bits = discrete_c & 0x03
    if country_bits == 0x00:
        return "TNI_AU"
    elif country_bits == 0x01:
        return "Bangladesh"
    else:
        return "Unknown"

def decode_packet(discrete_a, discrete_b, discrete_c):
    """Decode full packet based on mode"""
    mode = decode_mode(discrete_b)
    nav_source = decode_nav_source(discrete_b)
    country = decode_country(discrete_c)
    
    # Decode Discrete A based on mode
    if mode == "EADI":
        flags_a = decode_discrete_a_eadi(discrete_a)
        flags_b = decode_discrete_b_eadi(discrete_b)
        flags_c = decode_discrete_c_eadi(discrete_c)
    elif mode == "EHSI":
        flags_a = decode_discrete_a_ehsi(discrete_a)
        flags_b = decode_discrete_b_ehsi(discrete_b)
        flags_c = decode_discrete_c_ehsi(discrete_c)
    elif mode == "RDU":
        flags_a = decode_discrete_a_rdu(discrete_a)
        flags_b = decode_discrete_b_rdu(discrete_b)
        flags_c = decode_discrete_c_rdu(discrete_c)
    else:
        flags_a = flags_b = flags_c = ['Unknown']
    
    return {
        'mode': mode,
        'nav_source': nav_source,
        'country': country,
        'flags_a': ', '.join(flags_a),
        'flags_b': ', '.join(flags_b),
        'flags_c': ', '.join(flags_c)
    }

def main():
    global packet_count
    
    print_header()
    
    try:
        # Open serial port
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT)
        print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud\n")
        
        # Flush input buffer
        ser.reset_input_buffer()
        
        print(f"{'Time':<12} {'Mode':<6} {'Nav':<10} {'Country':<12} {'Discrete A Flags':<40} {'Discrete B Flags':<30} {'Discrete C Flags':<30}")
        print("-" * 150)
        
        buffer = bytearray()
        last_display_time = 0
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
                        
                        # Parse packet
                        discrete_a = packet[2]
                        discrete_b = packet[3]
                        discrete_c = packet[4]
                        
                        # Decode
                        decoded = decode_packet(discrete_a, discrete_b, discrete_c)
                        
                        # Store latest data
                        latest_data = {
                            'timestamp': datetime.now().strftime("%H:%M:%S.%f")[:-3],
                            **decoded
                        }
                        
                        packet_count += 1
                        
                        # Display every N seconds
                        current_time = time.time()
                        if current_time - last_display_time >= DISPLAY_INTERVAL:
                            if latest_data:
                                print(f"{latest_data['timestamp']:<12} {latest_data['mode']:<6} {latest_data['nav_source']:<10} "
                                      f"{latest_data['country']:<12} {latest_data['flags_a']:<40} "
                                      f"{latest_data['flags_b']:<30} {latest_data['flags_c']:<30}")
                                last_display_time = current_time
                    else:
                        break
            
            # Small delay to prevent CPU hogging
            time.sleep(0.001)
    
    except serial.SerialException as e:
        print(f"\nSerial Error: {e}")
        print(f"\nTroubleshooting:")
        print(f"  1. Check if port {SERIAL_PORT} is correct")
        print(f"  2. Check if port is not used by another program")
        print(f"  3. Try different COM port number")
        return
    
    except KeyboardInterrupt:
        print(f"\n\nMonitoring stopped by user")
        print(f"\nTotal packets decoded: {packet_count}")
    
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print(f"\nSerial port {SERIAL_PORT} closed")

if __name__ == "__main__":
    main()
