#
# from flask import Flask, request, jsonify, send_from_directory
# from flask_cors import CORS
# from pymongo import MongoClient
# import os
# from werkzeug.utils import secure_filename
# import re
# from bson import ObjectId
# from datetime import datetime
#
# app = Flask(__name__)
# CORS(app)
#
# @app.route("/")
# def home():
#     return "Missing Person Backend API is running successfully!"
# # ===========================
# # MongoDB Connection
# # ===========================
#
# # ===========================
# # MongoDB Connection
# # ===========================
#
# MONGO_URI = "mongodb+srv://render_user:Vanshika0509@cluster0.6ds8ydm.mongodb.net/missing_person_db"
#
# client = MongoClient(MONGO_URI)
#
# try:
#     client.server_info()
#     print("MongoDB Connected Successfully")
# except Exception as e:
#     print("MongoDB Connection Failed:", e)
#
# db = client["missing_person_db"]
# collection = db["user_login_details"]
#
# # ===========================
# # Upload Folder Setup
# # ===========================
#
# UPLOAD_FOLDER = "uploads/photos"
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
#
# # ===========================
# # Submit Route
# # ===========================
#
# @app.route("/submit", methods=["POST"])
# def submit():
#     data = request.form
#     photo = request.files.get("photo")
#
#
#     # ===============================
#     # 🔥 PHONE VALIDATION STARTS HERE
#     # ===============================
#     phone_number = data.get("public-familyPhone", "").strip()
#
#     if not re.match(r'^[6-9]\d{9}$', phone_number):
#         return jsonify({
#             "error": "Invalid Indian phone number (must be 10 digits and start with 6-9)"
#         }), 400
#     # ===============================
#     # 🔥 PHONE VALIDATION ENDS HERE
#     # ===============================
#
#     # ===============================
#     # 🔥 DATE VALIDATION STARTS HERE
#     # ===============================
#     last_seen = data.get("public-dateTime")
#
#     if not last_seen:
#         return jsonify({
#             "error": "Last seen date & time is required."
#         }), 400
#
#     try:
#         selected_date = datetime.fromisoformat(last_seen)
#         current_date = datetime.now()
#
#         if selected_date > current_date:
#             return jsonify({
#                 "error": "Future date is not allowed."
#             }), 400
#     except ValueError:
#         return jsonify({
#             "error": "Invalid date format."
#         }), 400
#     # ===============================
#     # 🔥 DATE VALIDATION ENDS HERE
#     # ===============================
#
#     photo_path = None
#
#     if photo:
#         filename = secure_filename(photo.filename)
#         photo_path = os.path.join(UPLOAD_FOLDER, filename)
#         photo.save(photo_path)
#
#     document = {
#         "full_name": data.get("public-fullName"),
#         "age": data.get("public-age"),
#         "gender": data.get("gender"),
#         "language_spoken": data.get("language_spoken"),
#         "last_seen_location": data.get("public-location"),
#         "last_seen_datetime": data.get("public-dateTime"),
#         "clothing_description": data.get("clothing_description"),
#         "general_description": data.get("general_description"),
#         "medical_condition": data.get("medical_condition"),
#         "contact_name": data.get("public-familyName"),
#         "contact_phone": phone_number,
#         "photo_path": photo_path,
#         "status": "Missing"
#     }
#
#     collection.insert_one(document)
#
#     return jsonify({"message": "Report submitted successfully"})
#
# @app.route("/uploads/photos/<filename>")
# def get_photo(filename):
#     return send_from_directory("uploads/photos", filename)
#
# # ===========================
# # Get All Missing Reports
# # ===========================
#
# @app.route("/get-missing-reports", methods=["GET"])
# def get_missing_reports():
#     reports = list(collection.find())
#
#     # Convert ObjectId to string
#     for r in reports:
#         r["_id"] = str(r["_id"])
#
#     return jsonify(reports)
# # ===========================
# # Get All Reports (with status)
# # ===========================
#
# @app.route("/get-reports", methods=["GET"])
# def get_reports():
#     reports = list(collection.find())
#
#     for r in reports:
#         r["_id"] = str(r["_id"])
#         r["status"] = r.get("status", "Missing")  # default status
#
#     return jsonify(reports)
# # ===========================
# # Mark Report as Found
# # ===========================
#
# @app.route("/mark-found/<report_id>", methods=["POST"])
# def mark_found(report_id):
#     collection.update_one(
#         {"_id": ObjectId(report_id)},
#         {"$set": {"status": "Found"}}
#     )
#
#     return jsonify({"message": "Marked as Found"})
#
#
# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5001, debug=True)
#


from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pymongo import MongoClient
from bson import ObjectId
import os
import re
import uuid
from datetime import datetime
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
collection = db["user_login_details"]

# ===========================
# Upload Folder
# ===========================
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads/photos")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ===========================
# Serve Static Frontend Files
# ===========================
STATIC_DIR = os.path.join(os.getcwd(), "static")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ===========================
# Home Route — serves index.html
# ===========================
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if not os.path.exists(index_path):
        return HTMLResponse(content="<h2>Frontend not found. Place index.html inside the /static folder.</h2>", status_code=404)
    with open(index_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# ===========================
# Submit Route
# ===========================
@app.post("/submit")
async def submit(
    public_fullName: str = Form(...),
    public_age: str = Form(...),
    gender: str = Form(...),
    language_spoken: Optional[str] = Form(None),
    public_location: str = Form(...),
    public_dateTime: str = Form(...),
    clothing_description: Optional[str] = Form(None),
    general_description: Optional[str] = Form(None),
    medical_condition: Optional[str] = Form(None),
    public_familyName: str = Form(...),
    public_familyPhone: str = Form(...),
    photo: UploadFile = File(None)
):
    # Phone validation
    phone_number = public_familyPhone.strip()
    if not re.match(r'^[6-9]\d{9}$', phone_number):
        raise HTTPException(status_code=400, detail="Invalid Indian phone number")

    # Date validation
    if not public_dateTime:
        raise HTTPException(status_code=400, detail="Date & time required")

    try:
        selected_date = datetime.fromisoformat(public_dateTime)
        if selected_date > datetime.now():
            raise HTTPException(status_code=400, detail="Future date not allowed")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    # Save photo
    photo_path = None
    if photo and photo.filename:
        ext = os.path.splitext(photo.filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

        with open(file_path, "wb") as f:
            f.write(await photo.read())

        photo_path = f"uploads/photos/{unique_filename}"

    # MongoDB document
    document = {
        "full_name": public_fullName,
        "age": public_age,
        "gender": gender,
        "language_spoken": language_spoken,
        "last_seen_location": public_location,
        "last_seen_datetime": public_dateTime,
        "clothing_description": clothing_description,
        "general_description": general_description,
        "medical_condition": medical_condition,
        "contact_name": public_familyName,
        "contact_phone": phone_number,
        "photo_path": photo_path,
        "status": "Missing"
    }

    result = collection.insert_one(document)
    print("Inserted ID:", result.inserted_id)

    return {"message": "Report submitted successfully"}

# ===========================
# Serve uploaded photos
# ===========================
@app.get("/uploads/photos/{filename}")
def get_photo(filename: str):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Photo not found")
    return FileResponse(file_path)

# ===========================
# Get Missing Reports
# ===========================
@app.get("/get-missing-reports")
def get_missing_reports():
    reports = list(collection.find())
    for r in reports:
        r["_id"] = str(r["_id"])
    return reports

# ===========================
# Get All Reports
# ===========================
@app.get("/get-reports")
def get_reports():
    reports = list(collection.find())
    for r in reports:
        r["_id"] = str(r["_id"])
        r["status"] = r.get("status", "Missing")
    return reports

# ===========================
# Mark as Found
# ===========================
@app.post("/mark-found/{report_id}")
def mark_found(report_id: str):
    collection.update_one(
        {"_id": ObjectId(report_id)},
        {"$set": {"status": "Found"}}
    )
    return {"message": "Marked as Found"}
