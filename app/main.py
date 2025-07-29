from fastapi import FastAPI
from .database import Base, engine

app = FastAPI()

# Create tables
Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "Receipt AI System is running"}
