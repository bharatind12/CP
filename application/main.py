from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import os
import serial
import time

app = Flask(__name__)

# SQLite configuration
DATABASE_URL = 'sqlite:///sqlite.db'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# Define SQLAlchemy ORM model
class SessionData(Base):
    __tablename__ = 'sessions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    sessionName = Column(String)
    threshold = Column(Integer)
    numberOfPenetrations = Column(Integer, default=0)
    numberOfTurns = Column(Integer, default=0)
    sensorValue = Column(Integer, default=0)
    status = Column(String, default='NO-GO')

Base.metadata.create_all(engine)

# Serial configuration
arduino = serial.Serial('/dev/ttyS0', 9600)  # Replace with your Arduino serial configuration
time.sleep(2)  # Wait for the serial connection to initialize

def send_command_to_arduino(command):
    arduino.write(command.encode())
    time.sleep(1)  # Give Arduino time to process the command
    response = arduino.readline().decode().strip()
    return response

app.mount("/", StaticFiles(directory="static",html = True), name="static")

@app.get("/", response_class=FileResponse)
async def root() -> Any:
        return "index.html"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit_form():
    data = request.json
    session_name = data.get('sessionName')
    threshold = int(data.get('threshold'))
    
    # Create new session in SQLite database
    session = SessionData(sessionName=session_name, threshold=threshold)
    session.add(session)
    session.commit()
    
    return jsonify({"message": "Form submitted successfully", "session_id": session.id})

@app.route('/go_down', methods=['POST'])
def go_down():
    data = request.json
    session_id = int(data.get('session_id'))
    
    # Retrieve session from SQLite database
    session = Session.query(SessionData).filter_by(id=session_id).first()
    
    session.numberOfTurns += 1
    session.sensorValue = int(send_command_to_arduino("GO_DOWN\n"))  # Get sensor value from Arduino
    session.status = 'NO-GO'
    
    if session.sensorValue >= session.threshold:
        session.numberOfPenetrations += 1
        session.numberOfTurns = 0
        session.status = 'GO-GO'
    
    Session.commit()
    
    return jsonify({
        'session_id': session.id,
        'numberOfPenetrations': session.numberOfPenetrations,
        'numberOfTurns': session.numberOfTurns,
        'sensorValue': session.sensorValue,
        'status': session.status
    })

@app.route('/retract', methods=['POST'])
def retract():
    data = request.json
    session_id = int(data.get('session_id'))
    
    # Retrieve session from SQLite database
    session = Session.query(SessionData).filter_by(id=session_id).first()
    
    session.numberOfPenetrations += 1
    session.numberOfTurns = 0
    session.status = 'NO-GO'
    
    send_command_to_arduino("RETRACT\n")
    
    Session.commit()
    
    return jsonify({
        'session_id': session.id,
        'numberOfPenetrations': session.numberOfPenetrations,
        'numberOfTurns': session.numberOfTurns,
        'sensorValue': session.sensorValue,
        'status': session.status
    })

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)