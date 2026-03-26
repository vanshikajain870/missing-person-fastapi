from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from datetime import datetime
import os
import uuid
from typing import Optional

app = FastAPI()

# ===========================
# CORS
# ===========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===========================
# MongoDB Connection
# ===========================
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise RuntimeError("MONGO_URI environment variable is not set!")

client = MongoClient(MONGO_URI)

try:
    client.server_info()
    print("MongoDB Connected Successfully")
except Exception as e:
    print("MongoDB Connection Failed:", e)

db = client["missing_person_db"]
inmates_collection = db["inmates"]

# ===========================
# Upload Folder Setup
# ===========================
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads/inmates")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ===========================
# Serve uploaded photos as static files
# ===========================
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ===========================
# Home Route
# ===========================
@app.get("/")
def home():
    return {"message": "Inmate Registration API is running successfully!"}

# ===========================
# Register Inmate Route
# ===========================
@app.post("/register-inmate")
async def register_inmate(
    inmate_id: str = Form(...),
    registration_no: str = Form(...),
    unique_id: Optional[str] = Form(None),
    status: str = Form(...),
    full_name: str = Form(...),
    dob: str = Form(...),
    gender: str = Form(...),
    languages: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    joining_date: str = Form(...),
    photo: Optional[UploadFile] = File(None)
):

    # ===========================
    # Date Validation
    # ===========================
    try:
        dob_date = datetime.fromisoformat(dob)
        joining_date_obj = datetime.fromisoformat(joining_date)
        current_date = datetime.now()

        if dob_date > current_date:
            raise HTTPException(status_code=400, detail="Future Date of Birth is not allowed")

        if joining_date_obj > current_date:
            raise HTTPException(status_code=400, detail="Future Joining Date is not allowed")

        if joining_date_obj < dob_date:
            raise HTTPException(status_code=400, detail="Joining date cannot be before Date of Birth")

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    # ===========================
    # Save Photo
    # ===========================
    photo_path = None
    if photo and photo.filename:
        ext = os.path.splitext(photo.filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

        with open(file_path, "wb") as f:
            f.write(await photo.read())

        photo_path = f"uploads/inmates/{unique_filename}"

    # ===========================
    # Save to MongoDB
    # ===========================
    inmate_document = {
        "inmate_id": inmate_id,
        "registration_no": registration_no,
        "unique_id": unique_id,
        "status": status,
        "full_name": full_name,
        "dob": dob,
        "gender": gender,
        "languages": languages,
        "address": address,
        "joining_date": joining_date,
        "photo_path": photo_path
    }

    result = inmates_collection.insert_one(inmate_document)
    print("Inserted Inmate ID:", result.inserted_id)

    return {"message": "Inmate registered successfully"}
