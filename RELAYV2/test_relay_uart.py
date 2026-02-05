
import serial
import time
from datetime import datetime

# ===== CONFIGURATION =====
SERIAL_PORT = 'COM14'# Port RELAYV2
BAUD_RATE = 115200
TIMEOUT = 1  # seconds

# ===== STATISTICS =====
packet_count = 0
error_count = 0
last_time = None
intervals = []

def print_header():
    """Print header information"""
    print("=" * 70)
    print("RELAYV2 UART Monitor - Testing 0x99 0xA5 Transmission")
    print("=" * 70)
    print(f"Port: {SERIAL_PORT}")
    print(f"Baud Rate: {BAUD_RATE}")
    print(f"Expected Interval: ~5ms (200 Hz)")
    print(f"Expected Packet: [0x99, 0xA5, value]")
    print("=" * 70)
    print("\nPress Ctrl+C to stop monitoring...\n")

def format_hex(data):
    """Format bytes as hex string"""
    return ' '.join([f'{b:02X}' for b in data])

def calculate_stats():
    """Calculate and display statistics"""
    if len(intervals) > 0:
        avg_interval = sum(intervals) / len(intervals)
        min_interval = min(intervals)
        max_interval = max(intervals)
        frequency = 1000.0 / avg_interval if avg_interval > 0 else 0
        
        print("\n" + "=" * 70)
        print("STATISTICS")
        print("=" * 70)
        print(f"Total Packets Received: {packet_count}")
        print(f"Total Errors: {error_count}")
        print(f"Success Rate: {(packet_count/(packet_count+error_count)*100):.2f}%" if (packet_count+error_count) > 0 else "N/A")
        print(f"\nInterval Statistics:")
        print(f"  Average: {avg_interval:.2f} ms ({frequency:.1f} Hz)")
        print(f"  Minimum: {min_interval:.2f} ms")
        print(f"  Maximum: {max_interval:.2f} ms")
        print(f"  Target:  5.00 ms (200 Hz)")
        print("=" * 70)

def main():
    global packet_count, error_count, last_time
    
    print_header()
    
    try:
        # Open serial port
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT)
        print(f"✅ Connected to {SERIAL_PORT} at {BAUD_RATE} baud\n")
        
        # Flush input buffer
        ser.reset_input_buffer()
        
        print(f"{'Time':<12} {'Packet':<20} {'Interval':<12} {'Status':<20}")
        print("-" * 70)
        
        while True:
            # Read 3 bytes (expected packet size)
            if ser.in_waiting >= 3:
                data = ser.read(3)
                current_time = time.time()
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                
                # Calculate interval
                interval_ms = 0
                if last_time is not None:
                    interval_ms = (current_time - last_time) * 1000
                    intervals.append(interval_ms)
                    # Keep only last 100 intervals for stats
                    if len(intervals) > 100:
                        intervals.pop(0)
                
                last_time = current_time
                
                # Parse packet type
                if len(data) == 3:
                    packet_count += 1
                    
                    # Check if it's status packet (0x99 0xA5)
                    if data[0] == 0x99 and data[1] == 0xA5:
                        status = "✅ STATUS"
                        value = data[2]
                        packet_str = f"99 A5 {value:02X} (Status: {value})"
                    
                    # Check if it's ROME device packet (ID 0x01-0x05)
                    elif data[0] >= 0x01 and data[0] <= 0x05:
                        status = "✅ ROME"
                        device_id = data[0]
                        msb = data[1]
                        lsb = data[2]
                        raw_value = (msb << 8) | lsb
                        angle = raw_value / 10.0  # Decode angle (÷10)
                        packet_str = f"{device_id:02X} {msb:02X} {lsb:02X} (Dev{device_id}: {raw_value} = {angle:.1f}°)"
                    
                    # Unknown packet
                    else:
                        status = "❓ UNKNOWN"
                        packet_str = format_hex(data)
                    
                    interval_str = f"{interval_ms:.2f} ms" if interval_ms > 0 else "N/A"
                    print(f"{timestamp:<12} {packet_str:<45} {interval_str:<12} {status:<20}")
                    
                else:
                    error_count += 1
                    status = "❌ INVALID"
                    packet_str = format_hex(data)
                    interval_str = f"{interval_ms:.2f} ms" if interval_ms > 0 else "N/A"
                    
                    print(f"{timestamp:<12} {packet_str:<45} {interval_str:<12} {status:<20}")
            
            # Small delay to prevent CPU hogging
            time.sleep(0.001)
    
    except serial.SerialException as e:
        print(f"\n❌ Serial Error: {e}")
        print(f"\nTroubleshooting:")
        print(f"  1. Check if RELAYV2 is connected to {SERIAL_PORT}")
        print(f"  2. Check if port is not used by another program")
        print(f"  3. Try different COM port number")
        return
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Monitoring stopped by user")
        calculate_stats()
    
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print(f"\n✅ Serial port {SERIAL_PORT} closed")

if __name__ == "__main__":
    main()
