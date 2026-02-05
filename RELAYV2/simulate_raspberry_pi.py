"""
Simulate Raspberry Pi → RELAYV2
================================
Script ini mengirim packet 15-byte ke RELAYV2 UART1 (PA10)
untuk simulasi data dari Raspberry Pi.

RELAYV2 akan parse data dan forward ke ROME devices via UART2 (PA2)

Connection:
    USB-to-Serial TX → PA10 (RELAYV2 UART1 RX)
    GND → GND

Author: Antigravity AI Assistant
Date: 2026-01-29
"""

import serial
import time
from datetime import datetime

# ===== CONFIGURATION =====
SERIAL_PORT = 'COM11'# Port ke RELAYV2 UART1
BAUD_RATE = 115200
INTERVAL = 0.1  # Send every 100ms

def create_packet(device_values):
    """
    Create 15-byte packet for RELAYV2
    
    Format:
        [0xA5, 0x99, Discrete_A, Discrete_B, Discrete_C,
         Dev1_MSB, Dev1_LSB, Dev2_MSB, Dev2_LSB, Dev3_MSB, Dev3_LSB,
         Dev4_MSB, Dev4_LSB, Dev5_MSB, Dev5_LSB]
    
    Args:
        device_values: List of 5 integers (0-65535) for each device
    
    Returns:
        List of 15 bytes
    """
    packet = [
        0xA5, 0x99,           # Header (REQUIRED!)
        0x00, 0x00, 0x00,     # Discrete A, B, C (relay control)
    ]
    
    # Add device data (MSB, LSB for each device)
    for value in device_values:
        msb = (value >> 8) & 0xFF
        lsb = value & 0xFF
        packet.extend([msb, lsb])
    
    return packet

def main():
    print("=" * 70)
    print("Simulating Raspberry Pi → RELAYV2")
    print("=" * 70)
    print(f"Port: {SERIAL_PORT}")
    print(f"Baud Rate: {BAUD_RATE}")
    print(f"Interval: {INTERVAL * 1000:.0f} ms")
    print("=" * 70)
    
    # Ask user for auto-increment mode
    print("\n🔧 Configuration:")
    auto_increment = input("Auto-increment values? (y/n): ").lower() == 'y'
    
    print("\nPress Ctrl+C to stop...\n")
    
    try:
        # Open serial port
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"✅ Connected to {SERIAL_PORT}\n")
        
        packet_count = 0
        
        # Test values for 5 devices
        device_values = [
            0x1234,  # Device 1: 4660
            0x5678,  # Device 2: 22136
            0x9ABC,  # Device 3: 39612
            0xDEF0,  # Device 4: 57072
            0x1122,  # Device 5: 4386
        ]
        
        print(f"{'Time':<12} {'Packet':<8} {'Dev1':<8} {'Dev2':<8} {'Dev3':<8} {'Dev4':<8} {'Dev5':<8}")
        print("-" * 70)
        
        while True:
            # Create packet
            packet = create_packet(device_values)
            
            # Send packet
            ser.write(bytes(packet))
            packet_count += 1
            
            # Display with device breakdown
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            dev_str = ' '.join([f'{v:05d}' for v in device_values])
            
            print(f"{timestamp:<12} #{packet_count:04d}   {device_values[0]:05d}    {device_values[1]:05d}    {device_values[2]:05d}    {device_values[3]:05d}    {device_values[4]:05d}")
            
            # Auto-increment if enabled
            if auto_increment:
                for i in range(5):
                    device_values[i] = (device_values[i] + 100) % 65536
            
            time.sleep(INTERVAL)
    
    except serial.SerialException as e:
        print(f"\n❌ Serial Error: {e}")
        print(f"\nTroubleshooting:")
        print(f"  1. Check if RELAYV2 is connected to {SERIAL_PORT}")
        print(f"  2. Check if port is not used by another program")
        print(f"  3. Try different COM port number")
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user")
        print(f"\nTotal packets sent: {packet_count}")
    
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print(f"✅ Serial port {SERIAL_PORT} closed")

if __name__ == "__main__":
    main()
