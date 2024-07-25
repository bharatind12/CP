from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi_versioning import VersionedFastAPI, version
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import serial
import time
import re
import threading
import queue

# FastAPI application instance
app = FastAPI(
    title="Cone Penetrometer API",
    description="API for cone penetrometer operations.",
)

# SQLite configuration
DATABASE_URL = 'sqlite:///sqlite.db'
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define SQLAlchemy ORM model
class SessionData(Base):
    __tablename__ = 'sessions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    sessionName = Column(String)
    threshold = Column(Integer)
    numberOfPenetrations = Column(Integer, default=0)
    sensorValue = Column(Integer, default=0)
    status = Column(String, default='NO-GO')
    steps = Column(Integer, default=0)

Base.metadata.create_all(bind=engine)

class SessionCreate(BaseModel):
    sessionName: str
    threshold: int

class Session(BaseModel):
    id: int
    sessionName: str
    threshold: int
    numberOfPenetrations: int
    sensorValue: int
    status: str
    steps:int

    class Config:
        orm_mode = True

class SessionRequest(BaseModel):
    session_id: int

# Arduino setup
arduino = None
serial_port = '/dev/cone_penetrometer'
baud_rate = 9600
arduino_lock = threading.Lock()
command_queue = queue.Queue()
response_queue = queue.Queue()

# Cached sensor value
cached_sensor_value = 0
cache_lock = threading.Lock()

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

def send_command_to_arduino(command, wait_for_response=True):
    global arduino
    with arduino_lock:
        if arduino is None or not arduino.is_open:
            connect_to_arduino()
        if arduino is None:
            raise HTTPException(status_code=500, detail="Failed to connect to Arduino")

        try:
            arduino.write(command.encode())
            if not wait_for_response:
                return None

            time.sleep(0.1)  # Reduced wait time
            response = arduino.readline().decode().strip()
            return response
        except serial.SerialException as e:
            print(f"Error communicating with Arduino: {e}")
            arduino.close()
            arduino = None
            raise HTTPException(status_code=500, detail="Error communicating with Arduino")

def parse_sensor_value(response):
    match = re.search(r'\b([2-9]\d{2}|999)\b', response)
    if match:
        return int(match.group(1))
    raise ValueError("Invalid sensor value received")

def arduino_command_worker():
    while True:
        command = command_queue.get()
        try:
            if "RETRACT" in command:
                response = send_command_to_arduino(command, wait_for_response=True)
                response_queue.put(response)
            else:
                # Handle other commands as needed
                send_command_to_arduino(command, wait_for_response=False)
        except Exception as e:
            print(f"Error executing Arduino command: {e}")
            if "RETRACT" in command:
                response_queue.put(None)  # Put None in case of error
        command_queue.task_done()

def continuous_sensor_reading():
    global cached_sensor_value
    while True:
        try:
            response = send_command_to_arduino("SENSOR_VALUE\n")
            sensor_value = parse_sensor_value(response)
            with cache_lock:
                cached_sensor_value = sensor_value
            time.sleep(0.1)  # Read sensor value every 100ms
        except Exception as e:
            print(f"Error reading sensor value: {e}")
            time.sleep(1)  # Wait before retrying on error

# Start background threads
threading.Thread(target=arduino_command_worker, daemon=True).start()
threading.Thread(target=continuous_sensor_reading, daemon=True).start()

@app.post("/submit", response_model=Session)
def submit(request: SessionCreate):
    db = SessionLocal()
    try:
        session = SessionData(
            sessionName=request.sessionName,
            threshold=request.threshold,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return Session.from_orm(session)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.delete("/close_session/{session_id}")
def close_session(session_id: int):
    db = SessionLocal()
    try:
        session = db.query(SessionData).filter(SessionData.id == session_id).first()
        if session:
            db.delete(session)
            db.commit()
            return {"message": "Session closed successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/sensor_value")
def get_sensor_value():
    db = SessionLocal()
    try:
        with cache_lock:
            sensor_value = cached_sensor_value
        
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

@app.post("/go_down")
def go_down(request: SessionRequest):
    db = SessionLocal()
    try:
        session = db.query(SessionData).filter(SessionData.id == request.session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        command_queue.put("GO_DOWN\n")
        session.status = 'NO-GO'
        session.numberOfPenetrations += 1
        db.commit()
        return {
            "numberOfPenetrations": session.numberOfPenetrations,
            "status": session.status
            }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.post("/retract")
def retract(request: SessionRequest):
    db = SessionLocal()
    try:
        session = db.query(SessionData).filter(SessionData.id == request.session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        command_queue.put("RETRACT\n")
        
        # Wait for the response with a timeout
        try:
            response = response_queue.get(timeout=5)  # 5 second timeout
            if response is None:
                raise HTTPException(status_code=500, detail="Error communicating with Arduino")
            
            print("Arduino response:", response)
            
            # Parse the response to get the number of steps
            try:
                steps = int(response)
                session.steps = steps
                print("Steps:", steps)
            except ValueError:
                print("Invalid response from Arduino")
                steps = 0
            
            # Calculate distance
            distance = int(steps * 0.025)
            print("Distance:", distance)
            
        except queue.Empty:
            raise HTTPException(status_code=504, detail="Timeout waiting for Arduino response")
        session.status = 'GO-GO'
        
        db.commit()
        return {
            "status": session.status,
            "steps": steps,
            "distance": distance
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

app = VersionedFastAPI(app, version="1.0.0", prefix_format="/v{major}.{minor}", enable_latest=True)

app.mount("/", StaticFiles(directory="/app/static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)