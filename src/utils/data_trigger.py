import serial

# Configure the serial connection (adjust parameters as needed)
ser = serial.Serial(port='/dev/ttyUSB0', baudrate=9600, timeout=1)

try:
    while True:
        # Read data from the serial port
        data = ser.readline().decode().strip()  # Decode bytes to string and remove trailing newline
        print(f"Received data: {data}")

        # Check if the trigger condition is met (e.g., specific message or value)
        if "trigger" in data:
            # Perform your desired action here (e.g., start recording, activate a device, etc.)
            print("Trigger detected!")

except KeyboardInterrupt:
    print("\nExiting due to user interruption.")

finally:
    ser.close()  # Close the serial port when done