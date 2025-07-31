from fastapi import FastAPI
from .database import Base, engine
from .routes import upload, validate, process , process_v5, receipts
# process_v2, process_v3, process_v4

app = FastAPI()

# Create tables
Base.metadata.create_all(bind=engine)

app.include_router(upload.router)
app.include_router(validate.router)
app.include_router(process.router)
# app.include_router(process_v2.router)
# app.include_router(process_v3.router)
# app.include_router(process_v4.router)
app.include_router(process_v5.router)
app.include_router(receipts.router)

@app.get("/")
def root():
    return {"message": "Receipt AI System is running"}
