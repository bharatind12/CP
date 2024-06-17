from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi_versioning import VersionedFastAPI, version
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import time
import serial

# FastAPI application instance
app = FastAPI(
    title="Example Extension 4 API",
    description="API for an example extension that saves/loads data as files.",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SQLite configuration
DATABASE_URL = 'sqlite:///./sqlite.db'
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
    numberOfTurns = Column(Integer, default=0)
    sensorValue = Column(Integer, default=0)
    status = Column(String, default='NO-GO')

Base.metadata.create_all(bind=engine)

# Serial configuration
arduino = serial.Serial('/dev/ttyACM0', 9600)  # Replace with your Arduino serial configuration
time.sleep(10)  # Wait for the serial connection to initialize

class SessionCreate(BaseModel):
    sessionName: str
    threshold: int

class Session(BaseModel):
    id: int
    sessionName: str
    threshold: int
    numberOfPenetrations: int
    numberOfTurns: int
    sensorValue: int
    status: str

    class Config:
        orm_mode = True

# Placeholder function for Arduino communication
def send_command_to_arduino(command):
    arduino.write(command.encode())
    time.sleep(1)  # Simulate delay for Arduino processing
    # response = arduino.readline().decode().strip()

    response = arduino
    # response = "50"  # Placeholder response for debugging
    return response

@app.post("/submit", response_model=Session)
def submit_form(session_data: SessionCreate):
    db = SessionLocal()
    db_session = SessionData(**session_data.dict())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    db.close()
    return db_session

@app.post("/go_down", response_model=Session)
@version(1, 0)
def go_down(session_id: int = Query(...)):
    db = SessionLocal()
    session = db.query(SessionData).filter(SessionData.id == session_id).first()
    
    if not session:
        db.close()
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        session.numberOfTurns += 1
        session.sensorValue = int(send_command_to_arduino("GO_DOWN\n"))  # Get sensor value from Arduino
        session.status = 'NO-GO'
        
        if session.sensorValue >= session.threshold:
            session.numberOfPenetrations += 1
            session.numberOfTurns = 0
            session.status = 'GO-GO'
        
        db.commit()
        db.refresh(session)
        return session
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        db.close()

@app.post("/retract", response_model=Session)
@version(1, 0)
def retract(session_id: int = Query(...)):
    db = SessionLocal()
    session = db.query(SessionData).filter(SessionData.id == session_id).first()
    
    if not session:
        db.close()
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        session.numberOfPenetrations += 1
        session.numberOfTurns = 0
        session.status = 'NO-GO'
        
        send_command_to_arduino("RETRACT\n")
        
        db.commit()
        db.refresh(session)
        return session
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        db.close()

@app.get("/sensor_value", response_model=dict)
@version(1, 0)
def get_sensor_value():
    # Placeholder implementation for testing
    return {
        "sensorValue": 50,  # Simulated sensor value
        "status": "OK"  # Simulated status
    }

app = VersionedFastAPI(app, version_format='{major}.{minor}', prefix_format='/v{major}.{minor}')

# Static file serving configuration
app.mount("/", StaticFiles(directory="/app/static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
