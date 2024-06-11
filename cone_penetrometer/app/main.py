from flask import Flask, jsonify, request, send_from_directory
import serial
import time
import os

app = Flask(__name__, static_folder='templates')

# Configure the serial port
# ser = serial.Serial('/dev/tty*', 9600)  # Replace '/dev/ttyS0' with the appropriate serial port for your Arduino
ser = serial.Serial('/dev/ttyS3', 9600)
time.sleep(2)  # Wait for the serial connection to initialize

# Function to send command to Arduino and read response
def send_command(command):
    ser.write(command.encode())
    time.sleep(0.1)  # Wait for Arduino to process the command
    response = ser.readline().decode().strip()
    return response

@app.route('/send_command', methods=['POST'])
def handle_send_command():
    data = request.get_json()
    command = data.get('command')
    response = send_command(command)
    return jsonify({'response': response})

@app.route('/', methods=['GET'])
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        pass
    finally:
        ser.close()
