from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.api.router import api_router
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path="backend/.env")

app = FastAPI(title="CAD Assembly Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

os.makedirs("backend/storage", exist_ok=True)
app.mount("/api/files", StaticFiles(directory="backend/storage"), name="storage")

@app.get("/")
def read_root():
    return {"message": "CAD Assembly Generator API is running!"}
