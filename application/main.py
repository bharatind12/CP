from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
import os
from bson.objectid import ObjectId
import serial
import time

app = Flask(__name__)

# MongoDB configuration
client = MongoClient('mongodb://localhost:27017/')
db = client['cone_penetrometer']
collection = db['sessions']

# Serial configuration
arduino = serial.Serial('/dev/ttyS0', 9600)  # Replace 'COM3' with your Arduino's COM port
time.sleep(2)  # Wait for the serial connection to initialize

def send_command_to_arduino(command):
    arduino.write(command.encode())
    time.sleep(1)  # Give Arduino time to process the command
    response = arduino.readline().decode().strip()
    return response

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit_form():
    data = request.json
    session_name = data.get('sessionName')
    threshold = int(data.get('threshold'))
    session_data = {
        'sessionName': session_name,
        'threshold': threshold,
        'numberOfPenetrations': 0,
        'numberOfTurns': 0,
        'sensorValue': 0,
        'status': 'NO-GO'
    }
    result = collection.insert_one(session_data)
    return jsonify({"message": "Form submitted successfully", "session_id": str(result.inserted_id)})

@app.route('/go_down', methods=['POST'])
def go_down():
    data = request.json
    session_id = ObjectId(data.get('session_id'))
    session = collection.find_one({'_id': session_id})
    
    numberOfTurns = session['numberOfTurns'] + 1
    sensorValue = int(send_command_to_arduino("GO_DOWN\n"))  # Get sensor value from Arduino
    status = 'NO-GO'
    
    if sensorValue >= session['threshold']:
        numberOfPenetrations = session['numberOfPenetrations'] + 1
        numberOfTurns = 0
        status = 'GO-GO'
    else:
        numberOfPenetrations = session['numberOfPenetrations']

    collection.update_one({'_id': session_id}, {"$set": {
        'numberOfTurns': numberOfTurns,
        'sensorValue': sensorValue,
        'status': status,
        'numberOfPenetrations': numberOfPenetrations
    }})
    
    updated_session = collection.find_one({'_id': session_id})
    return jsonify(updated_session)

@app.route('/retract', methods=['POST'])
def retract():
    data = request.json
    session_id = ObjectId(data.get('session_id'))
    session = collection.find_one({'_id': session_id})
    
    numberOfPenetrations = session['numberOfPenetrations'] + 1
    numberOfTurns = 0
    status = 'NO-GO'
    
    retract_status = send_command_to_arduino("RETRACT\n")
    
    collection.update_one({'_id': session_id}, {"$set": {
        'numberOfPenetrations': numberOfPenetrations,
        'numberOfTurns': numberOfTurns,
        'status': status
    }})
    
    updated_session = collection.find_one({'_id': session_id})
    return jsonify(updated_session)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
