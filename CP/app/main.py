from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi_versioning import VersionedFastAPI, version
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import time
import serial
import logging

# FastAPI application instance
app = FastAPI(
    title="Example Extension 4 API",
    description="API for an example extension that saves/loads data as files.",
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
    steps = Column(Integer, default=0)
    sensorValue = Column(Integer, default=0)
    status = Column(String, default='NO-GO')

Base.metadata.create_all(engine)

# Serial configuration
arduino = None
serial_port = '/dev/ttyACM0'
baud_rate = 9600

def connect_to_arduino():
    global arduino
    try:
        arduino = serial.Serial(serial_port, baud_rate, timeout=1)
        time.sleep(2)  # Wait for the serial connection to initialize
    except serial.SerialException as e:
        logging.error(f"Error connecting to Arduino: {e}")
        arduino = None

connect_to_arduino()

class SessionCreate(BaseModel):
    sessionName: str
    threshold: int

class SessionRequest(BaseModel):
    session_id: int

class Session(BaseModel):
    id: int
    sessionName: str
    threshold: int
    numberOfPenetrations: int
    steps: int
    sensorValue: int
    status: str

    class Config:
        orm_mode = True

def send_command_to_arduino(command):
    global arduino
    if arduino is None or not arduino.is_open:
        connect_to_arduino()
        if arduino is None:
            raise HTTPException(status_code=500, detail="Failed to connect to Arduino")
    
    try:
        arduino.write(command.encode())
        time.sleep(1)  # Give Arduino time to process the command
        response = arduino.readline().decode().strip()
        if response == '':
            raise serial.SerialException("No response from Arduino")
        return response
    except serial.SerialException as e:
        logging.error(f"Error communicating with Arduino: {e}")
        arduino.close()
        arduino = None
        raise HTTPException(status_code=500, detail="Error communicating with Arduino")

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
        raise e
    finally:
        db.close()

@app.get("/sensor_value", response_model=Session)
def get_sensor_value():
    db = SessionLocal()
    try:
        # Send command to Arduino to get sensor value
        sensor_value = int(send_command_to_arduino("SENSOR_VALUE\n"))
        
        # Retrieve the session to update its sensor value and status
        session = db.query(SessionData).first()  # Assuming there is one active session
        if session:
            session.sensorValue = sensor_value
            # Update status based on sensor value
            session.status = 'GO-GO' if session.sensorValue >= session.threshold else 'NO-GO'
            
            db.commit()
            db.refresh(session)
            return Session.from_orm(session)
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

@app.post("/retract", response_model=Session)
def retract(request: SessionRequest):
    session_id = request.session_id
    db = SessionLocal()
    try:
        session = db.query(SessionData).filter(SessionData.id == session_id).first()
        
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session.steps=int(send_command_to_arduino("RETRACT\n"))
        
        session.numberOfPenetrations += 1
        if(session.steps==10000):
           session.status = "NO-GO"
        else:   
            session.status = 'GO-GO'
        
        db.commit()
        db.refresh(session)
        return Session.from_orm(session)
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

@app.post("/go_down", response_model=Session)
def go_down(request: SessionRequest):
    session_id = request.session_id
    db = SessionLocal()
    try:
        session = db.query(SessionData).filter(SessionData.id == session_id).first()
        
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        
        send_command_to_arduino("GO_DOWN\n")  # Get sensor value from Arduino
        session.sensorValue = int(send_command_to_arduino("SENSOR_VALUE\n"))
        session.status = 'NO-GO'
        
        # if session.sensorValue >= session.threshold:
        #     session.numberOfPenetrations += 1
        #     session.status = 'GO-GO'
        
        db.commit()
        db.refresh(session)
        return Session.from_orm(session)
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

@app.delete("/close_session/{session_id}")
def close_session(request: SessionRequest):
    session_id = request.session_id
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


app = VersionedFastAPI(app, version="1.0.0", prefix_format="/v{major}.{minor}", enable_latest=True)

app.mount("/", StaticFiles(directory="/app/static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
