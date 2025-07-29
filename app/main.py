from fastapi import FastAPI
from .database import Base, engine
from .routes import upload

app = FastAPI()

# Create tables
Base.metadata.create_all(bind=engine)

app.include_router(upload.router)

@app.get("/")
def root():
    return {"message": "Receipt AI System is running"}
