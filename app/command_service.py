from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from fastapi_versioning import VersionedFastAPI, version
from fastapi.staticfiles import StaticFiles
import serial
import time

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

def send_command_to_arduino(command, wait_for_response=False, retries=3):
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

class SessionRequest(BaseModel):
    session_id: int

@app.post("/go_down")
def go_down(request: SessionRequest):
    db = SessionLocal()
    try:
        session = db.query(SessionData).filter(SessionData.id == request.session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        send_command_to_arduino("GO_DOWN\n", wait_for_response=False)
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
        
        response = send_command_to_arduino("RETRACT\n")
        print("This is response in command_service"+ response)
        session.steps = int(response) 
        print("This is steps in command_service"+ session.steps)
        session.status = 'GO-GO'
        
        db.commit()
        return {"status": session.status,"steps":session.steps}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5002)