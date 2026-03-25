#
#
# from flask import Flask, request, jsonify
# from flask_cors import CORS
# from pymongo import MongoClient
# import os
# import re
# from datetime import datetime
#
# app = Flask(__name__)
# CORS(app)
#
# # ===========================
# # MongoDB Connection
# # ===========================
#
# MONGO_URI = "mongodb+srv://render_user:Vanshika0509@cluster0.6ds8ydm.mongodb.net/missing_person_db"  # For Render
# # For local testing you can temporarily hardcode
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
#
# found_collection = db["found_persons"]
#
# # ===========================
# # Found Person Route
# # ===========================
#
# @app.route("/found-person", methods=["POST"])
# def found_person():
#
#     data = request.get_json()
#
#     if not data:
#         return jsonify({"error": "No JSON data received"}), 400
#
#     required_fields = [
#         "found_location",
#         "found_datetime",
#         "contact_name",
#         "contact_number"
#     ]
#
#     for field in required_fields:
#         if field not in data or not str(data[field]).strip():
#             return jsonify({"error": f"{field} is required"}), 400
#
#     # 🔥 INDIAN PHONE VALIDATION
#     phone_number = data["contact_number"]
#
#     if not re.match(r'^[6-9]\d{9}$', phone_number):
#         return jsonify({
#             "error": "Invalid Indian phone number (must be 10 digits and start with 6-9)"
#         }), 400
#
#         # ===============================
#         # 🔥 DATE VALIDATION STARTS HERE
#         # ===============================
#     found_datetime = data.get("found_datetime")
#
#     if not found_datetime:
#         return jsonify({
#             "error": "Found date & time is required."
#         }), 400
#
#     try:
#         selected_date = datetime.fromisoformat(found_datetime)
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
#     # 🔥 Create MongoDB document
#     found_document = {
#         "found_location": data["found_location"],
#         "found_datetime": data["found_datetime"],
#         "contact_name": data["contact_name"],
#         "contact_number": phone_number
#     }
#
#     found_collection.insert_one(found_document)
#
#     return jsonify({"message": "Found person stored successfully"}), 200
#
#
# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5001, debug=True)


from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pymongo import MongoClient
import os
import re
from datetime import datetime

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
found_collection = db["found_persons"]

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
        return HTMLResponse(
            content="<h2>Frontend not found. Place index.html inside the /static folder.</h2>",
            status_code=404
        )
    with open(index_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# ===========================
# Request Body Schema
# ===========================
class FoundPersonRequest(BaseModel):
    found_location: str
    found_datetime: str
    contact_name:   str
    contact_number: str

# ===========================
# Found Person Route
# ===========================
@app.post("/found-person")
def found_person(data: FoundPersonRequest):

    # Phone validation
    phone_number = data.contact_number.strip()
    if not re.match(r'^[6-9]\d{9}$', phone_number):
        raise HTTPException(
            status_code=400,
            detail="Invalid Indian phone number (must be 10 digits and start with 6-9)"
        )

    # Date validation
    if not data.found_datetime:
        raise HTTPException(status_code=400, detail="Found date & time is required.")

    try:
        selected_date = datetime.fromisoformat(data.found_datetime)
        if selected_date > datetime.now():
            raise HTTPException(status_code=400, detail="Future date is not allowed.")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format.")

    # Save to MongoDB
    found_document = {
        "found_location": data.found_location,
        "found_datetime": data.found_datetime,
        "contact_name":   data.contact_name,
        "contact_number": phone_number
    }

    found_collection.insert_one(found_document)

    return {"message": "Found person stored successfully"}
