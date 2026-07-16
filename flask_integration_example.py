"""
flask_integration_example.py

Drop-in example of how to wire matcher.py into your existing BloodLink Flask app.
Copy the relevant parts into your app.py / routes file.
"""

from flask import Flask, request, jsonify
import sqlite3
from matcher import find_best_donors

app = Flask(__name__)
DB_PATH = "bloodlink.db"  # adjust to your actual DB path


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def haversine_km(lat1, lon1, lat2, lon2):
    from math import radians, sin, cos, sqrt, atan2
    R = 6371
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


@app.route("/api/match-donors", methods=["POST"])
def match_donors():
    """
    Expects JSON body: { "blood_group": "O+", "lat": 11.664, "lon": 78.146 }
    Returns ranked donor matches.
    """
    payload = request.get_json()
    recipient_bg = payload["blood_group"]
    recipient_lat, recipient_lon = payload["lat"], payload["lon"]

    conn = get_db()
    rows = conn.execute("""
        SELECT donor_id, blood_group, age, latitude, longitude,
               days_since_last_donation, past_donations,
               response_rate, avg_response_time_min, is_available_now
        FROM donors
    """).fetchall()
    conn.close()

    donors = []
    for r in rows:
        distance_km = haversine_km(recipient_lat, recipient_lon, r["latitude"], r["longitude"])
        donors.append({
            "donor_id": r["donor_id"],
            "blood_group": r["blood_group"],
            "age": r["age"],
            "distance_km": round(distance_km, 2),
            "days_since_last_donation": r["days_since_last_donation"],
            "past_donations": r["past_donations"],
            "response_rate": r["response_rate"],
            "avg_response_time_min": r["avg_response_time_min"],
            "is_available_now": r["is_available_now"],
        })

    result = find_best_donors({"blood_group": recipient_bg}, donors, top_n=10)
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)
