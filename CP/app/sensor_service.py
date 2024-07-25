from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, Column, Integer, String
from fastapi_versioning import VersionedFastAPI, version
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import serial
import time
import re

app = FastAPI()

# Database setup
DATABASE_URL = 'sqlite:///sqlite.db'
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class SessionData(Base):
    __tablename__ = 'sessions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    sessionName = Column(String)
    threshold = Column(Integer)
    numberOfPenetrations = Column(Integer, default=0)
    sensorValue = Column(Integer, default=0)
    status = Column(String, default='NO-GO')
    steps = Column(Integer, default=0)

# Arduino setup
arduino = None
serial_port = '/dev/cone_penetrometer'
baud_rate = 9600

def connect_to_arduino():
    global arduino
    retries = 5
    delay = 2

    for attempt in range(retries):
        try:
            arduino = serial.Serial(serial_port, baud_rate, timeout=1)
            time.sleep(1)  # Wait for the serial connection to initialize
            print("Connected to Arduino on /dev/cone_penetrometer")
            return
        except serial.SerialException as e:
            print(f"Attempt {attempt + 1}/{retries} - Error connecting to Arduino: {e}")
            arduino = None
            if attempt < retries - 1:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)

    raise HTTPException(status_code=500, detail="No Arduino found on /dev/cone_penetrometer")

connect_to_arduino()

def send_command_to_arduino(command, wait_for_response=True, retries=3):
    global arduino
    if arduino is None or not arduino.is_open:
        connect_to_arduino()
    if arduino is None:
        raise HTTPException(status_code=500, detail="Failed to connect to Arduino")

    for attempt in range(retries):
        try:
            arduino.write(command.encode())
            if not wait_for_response:
                return None  # Return immediately if not waiting for a response
            
            time.sleep(0.5)  # Give Arduino time to process the command
            
            response = arduino.readline().decode().strip()
            if response:
                return response
            
        except serial.SerialException as e:
            print(f"Attempt {attempt + 1} - Error communicating with Arduino: {e}")
            if attempt < retries - 1:
                time.sleep(1)  # Wait before retrying
                connect_to_arduino()  # Re-establish connection
            else:
                arduino.close()
                arduino = None
                raise HTTPException(status_code=500, detail="Error communicating with Arduino after retries")

    raise HTTPException(status_code=500, detail="No valid response from Arduino after retries")

def parse_sensor_value(response):
    # Extract a number between 200 and 999 from the response
    match = re.search(r'\b([2-9]\d{2}|999)\b', response)
    if match:
        return int(match.group(1))
    raise ValueError("Invalid sensor value received")

@app.get("/sensor_value")
def get_sensor_value():
    db = SessionLocal()
    try:
        response = send_command_to_arduino("SENSOR_VALUE\n")
        sensor_value = parse_sensor_value(response)
        
        session = db.query(SessionData).first()
        if session:
            session.sensorValue = sensor_value
            db.commit()
            db.refresh(session)
            return {"sensorValue": session.sensorValue, "status": session.status}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# app = VersionedFastAPI(app, version="1.0.0", prefix_format="/v{major}.{minor}", enable_latest=True)

# app.mount("/", StaticFiles(directory="/app/static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)