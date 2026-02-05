"""
UART Diagnostic Tool - Auto-detect stuck issues
================================================
Monitor UART and automatically detect:
- Stuck (no packets for N seconds)
- Packet rate drops
- Error patterns
- Possible root causes

Usage: python uart_diagnostic.py
"""

import serial
import time
from datetime import datetime
from collections import deque

# ===== CONFIGURATION =====
SERIAL_PORT = 'COM14'
BAUD_RATE = 115200
TIMEOUT = 1

# Diagnostic thresholds
STUCK_TIMEOUT = 5  # seconds - if no packet for this long, consider stuck
MIN_RATE_WARNING = 50  # Hz - warn if rate drops below this
RATE_CHECK_INTERVAL = 1  # seconds - check rate every N seconds

# ===== STATISTICS =====
total_packets = 0
error_count = 0
last_packet_time = None
packet_times = deque(maxlen=1000)  # Keep last 1000 packet timestamps

def analyze_stuck_cause(time_since_last, total_packets, avg_rate):
    """Analyze possible causes of stuck"""
    print("\n" + "="*80)
    print("🔴 STUCK DETECTED!")
    print("="*80)
    print(f"Time since last packet: {time_since_last:.1f} seconds")
    print(f"Total packets received: {total_packets:,}")
    print(f"Average rate before stuck: {avg_rate:.1f} Hz")
    
    print("\n📋 POSSIBLE CAUSES:")
    
    if total_packets < 100:
        print("  1. ❌ UART not initialized properly")
        print("     → Check if Raspi_UART_Start() is called in main()")
        print("     → Check UART pins (PA10 = RX)")
    
    elif total_packets < 1000:
        print("  1. ❌ Early crash - likely callback error")
        print("     → Check HAL_UART_RxCpltCallback() for buffer overflow")
        print("     → Check if rx_index/idx_payload exceed buffer size")
    
    elif total_packets < 10000:
        print("  1. ⚠️  Callback logic error")
        print("     → Check if rx_ready flag is reset properly")
        print("     → Check if rx_index gets stuck (should reset to 0)")
    
    elif total_packets < 100000:
        print("  1. ⚠️  UART error not handled")
        print("     → Check if HAL_UART_ErrorCallback() exists")
        print("     → Check if error flags are cleared")
    
    else:
        print("  1. ⚠️  Long-term stability issue")
        print("     → Possible memory corruption")
        print("     → Check for stack overflow")
        print("     → Check if volatile keyword used for shared variables")
    
    print("\n🔧 RECOMMENDED ACTIONS:")
    print("  1. Check STM32 debugger for crash/hardfault")
    print("  2. Add LED toggle in HAL_UART_RxCpltCallback() to confirm it's running")
    print("  3. Check UART error register (huart1.ErrorCode)")
    print("  4. Try reducing baud rate to 9600 for testing")
    print("="*80)

def print_header():
    """Print header"""
    print("="*80)
    print("UART Diagnostic Tool - Auto-detect Stuck Issues")
    print("="*80)
    print(f"Port: {SERIAL_PORT}")
    print(f"Baud: {BAUD_RATE}")
    print(f"Stuck timeout: {STUCK_TIMEOUT}s")
    print("="*80)
    print("\nMonitoring... (Press Ctrl+C to stop)\n")

def main():
    global total_packets, error_count, last_packet_time
    
    print_header()
    
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT)
        print(f"✅ Connected to {SERIAL_PORT}\n")
        
        ser.reset_input_buffer()
        
        last_rate_check = time.time()
        packets_since_last_check = 0
        current_rate = 0
        
        print(f"{'Time':<12} {'Total Packets':<15} {'Rate (Hz)':<12} {'Status':<30}")
        print("-"*80)
        
        while True:
            current_time = time.time()
            
            # Check for stuck
            if last_packet_time is not None:
                time_since_last = current_time - last_packet_time
                if time_since_last >= STUCK_TIMEOUT:
                    # Calculate average rate before stuck
                    if len(packet_times) > 1:
                        time_span = packet_times[-1] - packet_times[0]
                        avg_rate = len(packet_times) / time_span if time_span > 0 else 0
                    else:
                        avg_rate = 0
                    
                    analyze_stuck_cause(time_since_last, total_packets, avg_rate)
                    
                    # Wait for user to fix and restart
                    print("\nWaiting for packets to resume...")
                    last_packet_time = None  # Reset to avoid repeated analysis
            
            # Read data
            if ser.in_waiting >= 3:
                data = ser.read(3)
                if len(data) == 3:
                    total_packets += 1
                    packets_since_last_check += 1
                    now = time.time()
                    last_packet_time = now
                    packet_times.append(now)
            
            # Calculate rate every N seconds
            if current_time - last_rate_check >= RATE_CHECK_INTERVAL:
                current_rate = packets_since_last_check / RATE_CHECK_INTERVAL
                
                # Status
                if current_rate == 0:
                    status = "⏸️  NO PACKETS"
                elif current_rate < MIN_RATE_WARNING:
                    status = f"⚠️  LOW RATE (< {MIN_RATE_WARNING} Hz)"
                else:
                    status = "✅ OK"
                
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"{timestamp:<12} {total_packets:<15,} {current_rate:<12.1f} {status:<30}")
                
                packets_since_last_check = 0
                last_rate_check = current_time
            
            time.sleep(0.001)
    
    except serial.SerialException as e:
        print(f"\n❌ Serial Error: {e}")
        print(f"\nCheck:")
        print(f"  1. Is {SERIAL_PORT} the correct port?")
        print(f"  2. Is another program using this port?")
        print(f"  3. Is USB-Serial adapter connected?")
    
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Monitoring stopped by user")
        print(f"\n📊 FINAL STATISTICS:")
        print(f"  Total packets: {total_packets:,}")
        print(f"  Errors: {error_count}")
        
        if len(packet_times) > 1:
            time_span = packet_times[-1] - packet_times[0]
            avg_rate = len(packet_times) / time_span if time_span > 0 else 0
            print(f"  Average rate: {avg_rate:.1f} Hz")
            print(f"  Duration: {time_span:.1f} seconds")
        
        if total_packets > 0:
            print(f"\n✅ No stuck detected - system stable!")
    
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print(f"\n✅ Serial port closed")

if __name__ == "__main__":
    main()
