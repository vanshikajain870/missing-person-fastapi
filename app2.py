from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pymongo import MongoClient
from datetime import datetime, date
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
    print("✅ MongoDB Connected Successfully")
except Exception as e:
    print("❌ MongoDB Connection Failed:", e)

db = client["missing_person_db"]
inmates_collection = db["inmates"]

# ===========================
# Upload Folder Setup
# ===========================
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads", "inmates")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ===========================
# Serve uploaded photos as static files
# /uploads/inmates/filename.jpg
# ===========================
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ===========================
# Serve static frontend files (JS, CSS)
# ===========================
app.mount("/static", StaticFiles(directory="static"), name="static")

# ===========================
# Serve index.html at root
# ===========================
@app.get("/")
def serve_index():
    return FileResponse("index.html")

# ===========================
# Health check
# ===========================
@app.get("/health")
def health():
    return {"status": "ok", "message": "Inmate Registration API is running"}

# ===========================
# Register Inmate Route
# ===========================
@app.post("/register-inmate")
async def register_inmate(
    inmate_id:       str           = Form(...),
    registration_no: str           = Form(...),
    unique_id:       Optional[str] = Form(None),
    status:          str           = Form(...),
    full_name:       str           = Form(...),
    dob:             str           = Form(...),
    gender:          str           = Form(...),
    languages:       Optional[str] = Form(None),
    address:         Optional[str] = Form(None),
    joining_date:    str           = Form(...),
    photo: Optional[UploadFile]    = File(None)
):
    # ===========================
    # Date Validation
    # HTML date inputs send "YYYY-MM-DD" (date only, no time).
    # We use date.fromisoformat() which handles "YYYY-MM-DD" correctly
    # on all Python versions including Render's.
    # ===========================
    try:
        dob_date         = date.fromisoformat(dob)           # e.g. "2000-05-15"
        joining_date_obj = date.fromisoformat(joining_date)  # e.g. "2024-01-10"
        today            = date.today()

        if dob_date > today:
            raise HTTPException(
                status_code=400,
                detail="Future Date of Birth is not allowed"
            )

        if joining_date_obj > today:
            raise HTTPException(
                status_code=400,
                detail="Future Joining Date is not allowed"
            )

        if joining_date_obj < dob_date:
            raise HTTPException(
                status_code=400,
                detail="Joining date cannot be before Date of Birth"
            )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format: {str(e)}"
        )

    # ===========================
    # Save Photo with unique name
    # ===========================
    photo_path = None
    if photo and photo.filename:
        ext             = os.path.splitext(photo.filename)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        file_path       = os.path.join(UPLOAD_FOLDER, unique_filename)

        contents = await photo.read()
        with open(file_path, "wb") as f:
            f.write(contents)

        photo_path = f"uploads/inmates/{unique_filename}"

    # ===========================
    # Save to MongoDB
    # ===========================
    inmate_document = {
        "inmate_id":       inmate_id,
        "registration_no": registration_no,
        "unique_id":       unique_id,
        "status":          status,
        "full_name":       full_name,
        "dob":             dob,
        "gender":          gender,
        "languages":       languages,
        "address":         address,
        "joining_date":    joining_date,
        "photo_path":      photo_path,
        "created_at":      datetime.now().isoformat()
    }

    try:
        result = inmates_collection.insert_one(inmate_document)
        print("✅ Inserted Inmate ID:", result.inserted_id)
    except Exception as e:
        print("❌ MongoDB insert failed:", e)
        raise HTTPException(
            status_code=500,
            detail="Database error. Could not save inmate record."
        )

    return {"message": "Inmate registered successfully"}
