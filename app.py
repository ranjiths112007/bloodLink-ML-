import math
import os
import sqlite3
from flask import Flask, jsonify, request, send_file

from blood_rules import VALID_BLOOD_GROUPS
from matcher import find_best_donors, MODEL_VERSION

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "bloodlink.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(seed_demo=False):
    """Create persistent schema. Never drops existing production data."""
    conn = get_db()
    conn.execute("""CREATE TABLE IF NOT EXISTS donors (
        donor_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        blood_group TEXT NOT NULL,
        age INTEGER NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        days_since_last_donation INTEGER,
        past_donations INTEGER DEFAULT 0,
        response_rate REAL DEFAULT 0.5,
        avg_response_time_min REAL DEFAULT 30.0,
        is_available_now INTEGER DEFAULT 0,
        image_url TEXT
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS blood_requests (
        request_id INTEGER PRIMARY KEY AUTOINCREMENT,
        blood_group TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        max_distance_km REAL NOT NULL DEFAULT 30,
        urgency TEXT NOT NULL DEFAULT 'normal',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS donor_interactions (
        interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id INTEGER NOT NULL,
        donor_id INTEGER NOT NULL,
        rank_position INTEGER,
        predicted_probability REAL,
        contacted_at TEXT,
        response TEXT CHECK(response IN ('accepted','declined','no_response','completed')),
        response_time_min REAL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(request_id) REFERENCES blood_requests(request_id),
        FOREIGN KEY(donor_id) REFERENCES donors(donor_id)
    )""")
    conn.commit()
    conn.close()


def haversine_km(lat1, lon1, lat2, lon2):
    radius = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def error(message, code, status=400):
    return jsonify({"error": {"code": code, "message": message}}), status


@app.route("/")
def index():
    return send_file(os.path.join(BASE_DIR, "bloodlink.html"))


@app.route("/api/health")
def health():
    try:
        conn = get_db()
        donor_count = conn.execute("SELECT COUNT(*) FROM donors").fetchone()[0]
        conn.close()
        return jsonify({"status": "ok", "model_version": MODEL_VERSION, "donor_count": donor_count})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 503


@app.route("/api/match-donors", methods=["POST"])
def match_donors():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error("JSON request body is required.", "INVALID_JSON")

    blood_group = str(payload.get("blood_group", "")).strip().upper()
    if blood_group not in VALID_BLOOD_GROUPS:
        return error("Invalid blood group.", "INVALID_BLOOD_GROUP")

    try:
        lat = float(payload["lat"])
        lon = float(payload["lon"])
        max_distance = float(payload.get("max_distance", 30.0))
    except (KeyError, TypeError, ValueError):
        return error("lat and lon must be valid numbers.", "INVALID_LOCATION")

    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return error("Latitude must be -90..90 and longitude -180..180.", "INVALID_LOCATION")
    if not (1 <= max_distance <= 500):
        return error("max_distance must be between 1 and 500 km.", "INVALID_DISTANCE")

    conn = get_db()
    rows = conn.execute("SELECT donor_id,name,blood_group,age,latitude,longitude,days_since_last_donation,past_donations,response_rate,avg_response_time_min,is_available_now,image_url FROM donors").fetchall()
    conn.close()

    donors = []
    for row in rows:
        donor = dict(row)
        donor["distance_km"] = round(haversine_km(lat, lon, donor["latitude"], donor["longitude"]), 2)
        donors.append(donor)

    try:
        result = find_best_donors({"blood_group": blood_group}, donors, top_n=10, max_distance_km=max_distance)
    except RuntimeError as exc:
        return error(str(exc), "MODEL_UNAVAILABLE", 503)
    except ValueError as exc:
        return error(str(exc), "INVALID_REQUEST")
    return jsonify(result)


@app.route("/api/requests", methods=["POST"])
def create_request():
    payload = request.get_json(silent=True) or {}
    blood_group = str(payload.get("blood_group", "")).strip().upper()
    if blood_group not in VALID_BLOOD_GROUPS:
        return error("Invalid blood group.", "INVALID_BLOOD_GROUP")
    try:
        lat, lon = float(payload["lat"]), float(payload["lon"])
        max_distance = float(payload.get("max_distance", 30))
    except (KeyError, TypeError, ValueError):
        return error("Valid lat and lon are required.", "INVALID_LOCATION")
    urgency = str(payload.get("urgency", "normal")).lower()
    if urgency not in {"normal", "high", "critical"}:
        return error("urgency must be normal, high, or critical.", "INVALID_URGENCY")

    conn = get_db()
    cur = conn.execute("INSERT INTO blood_requests (blood_group,latitude,longitude,max_distance_km,urgency) VALUES (?,?,?,?,?)", (blood_group, lat, lon, max_distance, urgency))
    request_id = cur.lastrowid
    conn.commit()
    conn.close()
    return jsonify({"request_id": request_id, "status": "created"}), 201


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)
