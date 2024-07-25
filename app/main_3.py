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
    numberOfTurns = Column(Integer, default=0)
    sensorValue = Column(Integer, default=0)
    status = Column(String, default='NO-GO')

Base.metadata.create_all(engine)

# Serial configuration
arduino = serial.Serial('/dev/ttyACM0', 9600)  # Replace with your Arduino serial configuration
time.sleep(2)  # Wait for the serial connection to initialize

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
    numberOfTurns: int
    sensorValue: int
    status: str

    class Config:
        orm_mode = True

def send_command_to_arduino(command):
    arduino.write(command.encode())
    time.sleep(1)  # Give Arduino time to process the command
    response = arduino.readline().decode().strip()
    return response

@app.post("/submit", response_model=Session)
def submit_form(session_data: SessionCreate):
    db = SessionLocal()
    db_session = SessionData(**session_data.dict())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return Session.from_orm(db_session)





from pydantic import BaseModel

class SessionRequest(BaseModel):
    session_id: int

@app.post("/go_down", response_model=Session)
def go_down(request: SessionRequest):
    session_id = request.session_id
    with SessionLocal() as db:
        session = db.query(SessionData).filter(SessionData.id == session_id).first()
        
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")

        print(f"Go Down session: {session}")

        session.numberOfTurns += 1
        session.sensorValue = send_command_to_arduino("GO_DOWN\n")  # Get sensor value from Arduino
        session.status = 'NO-GO'
        
        print(f"Go Down session: {session.value}")

        if session.sensorValue >= session.threshold:
            session.numberOfPenetrations += 1
            session.numberOfTurns = 0
            session.status = 'GO-GO'
        
        db.commit()
        db.refresh(session)
        return Session.from_orm(session)

@app.post("/retract", response_model=Session)
def retract(request: SessionRequest):
    session_id = request.session_id
    with SessionLocal() as db:
        session = db.query(SessionData).filter(SessionData.id == session_id).first()
    
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.numberOfPenetrations += 1
    session.numberOfTurns = 0
    session.status = 'NO-GO'
    
    send_command_to_arduino("RETRACT\n")
    
    db.commit()
    db.refresh(session)
    return Session.from_orm(session)

app = VersionedFastAPI(app, version="1.0.0", prefix_format="/v{major}.{minor}", enable_latest=True)

app.mount("/", StaticFiles(directory="/app/static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
