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
    conn.execute("PRAGMA foreign_keys = ON")
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
    conn.execute("CREATE INDEX IF NOT EXISTS idx_donors_blood_group ON donors(blood_group)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_interactions_request ON donor_interactions(request_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_interactions_donor ON donor_interactions(donor_id)")
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


def parse_location(payload):
    try:
        lat, lon = float(payload["lat"]), float(payload["lon"])
        radius = float(payload.get("max_distance", 30))
    except (KeyError, TypeError, ValueError):
        raise ValueError("Valid lat and lon are required.")
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError("Latitude must be -90..90 and longitude -180..180.")
    if not (1 <= radius <= 500):
        raise ValueError("max_distance must be between 1 and 500 km.")
    return lat, lon, radius


@app.route("/")
def index():
    return send_file(os.path.join(BASE_DIR, "dashboard.html"))


@app.route("/api/health")
def health():
    try:
        conn = get_db()
        donor_count = conn.execute("SELECT COUNT(*) FROM donors").fetchone()[0]
        request_count = conn.execute("SELECT COUNT(*) FROM blood_requests").fetchone()[0]
        interaction_count = conn.execute("SELECT COUNT(*) FROM donor_interactions").fetchone()[0]
        conn.close()
        return jsonify({"status": "ok", "model_version": MODEL_VERSION, "donor_count": donor_count,
                        "request_count": request_count, "interaction_count": interaction_count})
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
        lat, lon, max_distance = parse_location(payload)
    except ValueError as exc:
        return error(str(exc), "INVALID_LOCATION" if "location" in str(exc).lower() or "latitude" in str(exc).lower() else "INVALID_DISTANCE")
    urgency = str(payload.get("urgency", "normal")).lower()
    if urgency not in {"normal", "high", "critical"}:
        return error("urgency must be normal, high, or critical.", "INVALID_URGENCY")

    conn = get_db()
    rows = conn.execute("SELECT donor_id,name,blood_group,age,latitude,longitude,days_since_last_donation,past_donations,response_rate,avg_response_time_min,is_available_now,image_url FROM donors").fetchall()
    conn.close()
    donors = []
    for row in rows:
        donor = dict(row)
        donor["distance_km"] = round(haversine_km(lat, lon, donor["latitude"], donor["longitude"]), 2)
        donors.append(donor)
    try:
        result = find_best_donors({"blood_group": blood_group, "urgency": urgency}, donors, top_n=10, max_distance_km=max_distance)
    except RuntimeError as exc:
        return error(str(exc), "MODEL_UNAVAILABLE", 503)
    except ValueError as exc:
        return error(str(exc), "INVALID_REQUEST")

    # Persist the request so every later contact/outcome can become training data.
    conn = get_db()
    cur = conn.execute("INSERT INTO blood_requests (blood_group,latitude,longitude,max_distance_km,urgency) VALUES (?,?,?,?,?)",
                       (blood_group, lat, lon, max_distance, urgency))
    request_id = cur.lastrowid
    conn.commit()
    conn.close()
    result["request_id"] = request_id
    return jsonify(result)


@app.route("/api/requests", methods=["POST"])
def create_request():
    payload = request.get_json(silent=True) or {}
    blood_group = str(payload.get("blood_group", "")).strip().upper()
    if blood_group not in VALID_BLOOD_GROUPS:
        return error("Invalid blood group.", "INVALID_BLOOD_GROUP")
    try:
        lat, lon, max_distance = parse_location(payload)
    except ValueError as exc:
        return error(str(exc), "INVALID_LOCATION")
    urgency = str(payload.get("urgency", "normal")).lower()
    if urgency not in {"normal", "high", "critical"}:
        return error("urgency must be normal, high, or critical.", "INVALID_URGENCY")
    conn = get_db()
    cur = conn.execute("INSERT INTO blood_requests (blood_group,latitude,longitude,max_distance_km,urgency) VALUES (?,?,?,?,?)",
                       (blood_group, lat, lon, max_distance, urgency))
    request_id = cur.lastrowid
    conn.commit(); conn.close()
    return jsonify({"request_id": request_id, "status": "created"}), 201


@app.route("/api/interactions", methods=["POST"])
def log_interaction():
    payload = request.get_json(silent=True) or {}
    try:
        donor_id = int(payload["donor_id"])
        predicted = float(payload.get("predicted_probability", 0))
        rank = int(payload.get("rank_position", 0))
    except (KeyError, TypeError, ValueError):
        return error("donor_id, predicted_probability and rank_position are required.", "INVALID_INTERACTION")
    response_value = str(payload.get("response", "no_response")).lower()
    if response_value not in {"accepted", "declined", "no_response", "completed"}:
        return error("Invalid response outcome.", "INVALID_RESPONSE")
    conn = get_db()
    donor = conn.execute("SELECT donor_id FROM donors WHERE donor_id=?", (donor_id,)).fetchone()
    if donor is None:
        conn.close(); return error("Donor not found.", "DONOR_NOT_FOUND", 404)
    request_id = payload.get("request_id")
    if request_id is None:
        # Keep the demo resilient if a client logs an interaction without first creating a request.
        try:
            lat, lon, radius = parse_location(payload)
        except ValueError:
            lat, lon, radius = 13.0827, 80.2707, 30.0
        bg = str(payload.get("blood_group", "O+")).strip().upper()
        if bg not in VALID_BLOOD_GROUPS: bg = "O+"
        cur = conn.execute("INSERT INTO blood_requests (blood_group,latitude,longitude,max_distance_km,urgency) VALUES (?,?,?,?,?)",
                           (bg, lat, lon, radius, "normal"))
        request_id = cur.lastrowid
    try:
        request_id = int(request_id)
    except (TypeError, ValueError):
        conn.close(); return error("Invalid request_id.", "INVALID_REQUEST_ID")
    exists = conn.execute("SELECT request_id FROM blood_requests WHERE request_id=?", (request_id,)).fetchone()
    if exists is None:
        conn.close(); return error("Request not found.", "REQUEST_NOT_FOUND", 404)
    cur = conn.execute("""INSERT INTO donor_interactions
        (request_id,donor_id,rank_position,predicted_probability,contacted_at,response,response_time_min)
        VALUES (?,?,?,?,CURRENT_TIMESTAMP,?,?)""",
        (request_id, donor_id, rank, max(0, min(1, predicted)), response_value,
         payload.get("response_time_min")))
    interaction_id = cur.lastrowid
    conn.commit(); conn.close()
    return jsonify({"interaction_id": interaction_id, "request_id": request_id, "status": "logged"}), 201


@app.route("/api/requests/<int:request_id>/interactions")
def request_interactions(request_id):
    conn = get_db()
    rows = conn.execute("""SELECT i.*, d.name, d.blood_group FROM donor_interactions i
                           JOIN donors d ON d.donor_id=i.donor_id
                           WHERE i.request_id=? ORDER BY i.created_at DESC""", (request_id,)).fetchall()
    conn.close()
    return jsonify({"request_id": request_id, "interactions": [dict(r) for r in rows]})


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)
