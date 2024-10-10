import serial
import time

# Replace 'COMx' with the correct port (e.g., COM3 for Windows, /dev/ttyUSB0 for Linux)
bluetooth_port = 'COM8'
baud_rate = 9600  # Default baud rate for HC-06

# Connect to HC-06
try:
    ser = serial.Serial(bluetooth_port, baud_rate, timeout=1)
    print(f"Connected to {bluetooth_port}")
except serial.SerialException:
    print(f"Failed to connect to {bluetooth_port}")
    exit()

# Send command to Arduino to turn on the LED
time.sleep(2)  # Wait for connection to stabilize
ser.write(b'1')  # Send '1' to turn on the LED

# Read response from Arduino
response = ser.readline().decode().strip()
print(f"Arduino response: {response}")

# Close the connection
ser.close()
