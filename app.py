import os
import math
import sqlite3
from flask import Flask, request, jsonify, send_file
from matcher import find_best_donors

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bloodlink.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def haversine_km(lat1, lon1, lat2, lon2):
    """Computes geographical distance in kilometers between two lat/lon coordinates."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2)
    return R * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def init_db():
    """Initializes the database, drops existing donors table, and seeds with 43 donors near Chennai."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS donors")
    cursor.execute("""
        CREATE TABLE donors (
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
        )
    """)
    conn.commit()

    # Seed exactly 43 donors centered around Chennai (13.0827, 80.2707)
    lat_ref, lon_ref = 13.0827, 80.2707

    import random
    random.seed(42)  # For reproducible generator values

    names_pool = [
        "Arjun Kumar", "Divya Ramesh", "Karthik S", "Meena Priya", "Vignesh R",
        "Sowmya Iyer", "Naveen T", "Priya Dharshini", "Rahul Krishnan", "Kavya Suresh",
        "Suresh Kumar", "Anjali Sharma", "Vikram Singh", "Lakshmi Devi", "Rajesh V",
        "Shalini R", "Mohan Lal", "Sneha Gupta", "Manoj Nair", "Deepa J",
        "Prem Chand", "Harini S", "Balaji E", "Gayathri K", "Ram Prasath",
        "Aravind Swamy", "Nisha Patel", "Prakash Raj", "Keerthi Reddy", "Sanjay Dutt",
        "Aisha Begum", "Vijay Chandar", "Shruthi Hariharan", "Aditya Roy", "Geetha Sen",
        "Rohan Mehra", "Pooja Hegde", "Siddharth Rao", "Aparna Pillai", "Madhavan R",
        "Nivedita Bose", "Ketan Mehta", "Swara Bhaskar", "Gautam Gambhir", "Meera Jasmine"
    ]

    blood_groups_pool = ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"]

    def get_coords(dist_km, angle_rad):
        lat_off = (dist_km * math.cos(angle_rad)) / 111.32
        lon_off = (dist_km * math.sin(angle_rad)) / (111.32 * math.cos(math.radians(lat_ref)))
        return round(lat_ref + lat_off, 6), round(lon_ref + lon_off, 6)

    for i in range(43):
        name = names_pool[i % len(names_pool)]
        bg = random.choice(blood_groups_pool)
        age = random.randint(18, 65)

        # Distance: random between 1.0 and 38.0 km
        dist = random.uniform(1.0, 38.0)
        angle = random.uniform(0, 2 * math.pi)
        lat, lon = get_coords(dist, angle)

        # Days since last donation: 15% first-time donors, rest 30 to 600 days
        if random.random() < 0.15:
            days = None
            past = 0
            resp = 0.5
            avg_time = 30.0
        else:
            days = random.randint(30, 500)
            past = random.randint(1, 18)
            resp = round(random.uniform(0.35, 0.99), 2)
            avg_time = round(random.uniform(4.0, 85.0), 1)

        avail = 1 if random.random() < 0.75 else 0
        img = f"https://i.pravatar.cc/100?img={(i % 70) + 1}"

        cursor.execute("""
            INSERT INTO donors (name, blood_group, age, latitude, longitude,
                                days_since_last_donation, past_donations,
                                response_rate, avg_response_time_min, is_available_now, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, bg, age, lat, lon, days, past, resp, avg_time, avail, img))

    conn.commit()
    print("Database drop-recreated and seeded with 43 Chennai donors.")
    conn.close()


@app.route("/")
def index():
    return send_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), "bloodlink.html"))


@app.route("/api/match-donors", methods=["POST"])
def match_donors():
    """
    POST payload schema:
    {
      "blood_group": "O+",
      "lat": 13.0827,
      "lon": 80.2707,
      "max_distance": 30.0
    }
    """
    payload = request.get_json() or {}
    recipient_bg = payload.get("blood_group", "O+")
    recipient_lat = float(payload.get("lat", 13.0827))
    recipient_lon = float(payload.get("lon", 80.2707))
    max_distance = float(payload.get("max_distance", 30.0))

    conn = get_db()
    rows = conn.execute("""
        SELECT donor_id, name, blood_group, age, latitude, longitude,
               days_since_last_donation, past_donations,
               response_rate, avg_response_time_min, is_available_now, image_url
        FROM donors
    """).fetchall()
    conn.close()

    donors_list = []
    for r in rows:
        distance_km = haversine_km(recipient_lat, recipient_lon, r["latitude"], r["longitude"])
        donors_list.append({
            "donor_id": r["donor_id"],
            "name": r["name"],
            "blood_group": r["blood_group"],
            "age": r["age"],
            "latitude": r["latitude"],
            "longitude": r["longitude"],
            "distance_km": round(distance_km, 2),
            "days_since_last_donation": r["days_since_last_donation"],
            "past_donations": r["past_donations"],
            "response_rate": r["response_rate"],
            "avg_response_time_min": r["avg_response_time_min"],
            "is_available_now": r["is_available_now"],
            "image_url": r["image_url"],
        })

    # Call matcher pipeline returning up to 43 matches
    result = find_best_donors(
        {"blood_group": recipient_bg},
        donors_list,
        top_n=43,
        max_distance_km=max_distance
    )
    return jsonify(result)


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)
