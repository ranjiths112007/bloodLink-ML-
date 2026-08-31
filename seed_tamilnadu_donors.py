import math
import os
import random
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("BLOODLINK_DATA_DIR", os.path.join(BASE_DIR, "data"))
DB_PATH = os.environ.get("BLOODLINK_DB_PATH", os.path.join(DATA_DIR, "bloodlink.db"))

MALE_NAMES = [
    "Arjun", "Karthik", "Vignesh", "Naveen", "Rahul", "Suresh", "Vikram", "Rajesh", "Mohan", "Manoj",
    "Prem", "Balaji", "Ram", "Aravind", "Prakash", "Sanjay", "Vijay", "Aditya", "Rohan", "Siddharth",
    "Madhavan", "Ketan", "Gautam", "Dinesh", "Saravanan", "Murugan", "Santhosh", "Gokul", "Ganesh", "Ashok",
    "Prashanth", "Surya", "Manikandan", "Senthil", "Venkat", "Anand", "Deepak", "Hari", "Jayaram", "Kannan",
    "Logesh", "Mithun", "Narendran", "Pavithran", "Raghunath", "Srinivasan", "Tamilarasan", "Udhaya", "Vimal", "Yogesh",
    "Abishek", "Balamurugan", "Chandru", "Dhanush", "Elango", "Giridhar", "Hemachandran", "Ilango", "Jeeva", "Kuberan",
    "Loganathan", "Muralidharan", "Niranjan", "Parthiban", "Raghavan", "Subash", "Thirunavukkarasu", "Varun", "Yuvaraj"
]

FEMALE_NAMES = [
    "Divya", "Meena", "Sowmya", "Priya", "Kavya", "Anjali", "Lakshmi", "Shalini", "Sneha", "Deepa",
    "Harini", "Gayathri", "Nisha", "Keerthi", "Aisha", "Shruthi", "Geetha", "Pooja", "Aparna", "Nivedita",
    "Swara", "Meera", "Anitha", "Bhuvaneswari", "Chitra", "Dharani", "Ezhil", "Janani", "Kalpana", "Latha",
    "Malathi", "Nandhini", "Pavithra", "Radha", "Revathi", "Sandhya", "Uma", "Vidya", "Yamuna", "Archana",
    "Bharathi", "Deepika", "Hemalatha", "Indumathi", "Kavitha", "Monisha", "Preethi", "Rajeswari", "Sangeetha", "Thangam",
    "Abirami", "Bhavani", "Dhanalakshmi", "Gowri", "Janaki", "Kowsalya", "Mythili", "Nithya", "Renu", "Sangeetha"
]

LAST_NAMES = [
    "Kumar", "Ramesh", "Subramanian", "Iyer", "Krishnan", "Suresh", "Singh", "Devi", "Gupta", "Nair",
    "Chandran", "Hariharan", "Pillai", "Bose", "Priya", "Reddy", "Patel", "Raj", "Begum", "Sen",
    "Rao", "Mehra", "Hegde", "Bhaskar", "Gambhir", "Jasmine", "S", "R", "K", "V",
    "M", "N", "T", "P", "E", "G", "J", "B", "A", "C", "Mani", "Sundaram", "Narayanan", "Prabhu", "Velan"
]

BLOOD_GROUPS = ["O+", "A+", "B+", "AB+", "O-", "A-", "B-", "AB-"]
BLOOD_PROBS = [0.35, 0.25, 0.25, 0.07, 0.03, 0.02, 0.02, 0.01]

CLUSTERS = [
    # Chennai Neighborhoods (High Density ~220 donors)
    {"name": "Chennai Central / Egmore", "lat": 13.0827, "lon": 80.2707, "radius": 3.0, "count": 20},
    {"name": "T. Nagar / Kodambakkam", "lat": 13.0418, "lon": 80.2341, "radius": 3.0, "count": 20},
    {"name": "Anna Nagar / Shenoy Nagar", "lat": 13.0850, "lon": 80.2101, "radius": 3.0, "count": 20},
    {"name": "Velachery / Madipakkam", "lat": 12.9815, "lon": 80.2180, "radius": 4.0, "count": 20},
    {"name": "Adyar / Besant Nagar", "lat": 13.0012, "lon": 80.2565, "radius": 3.0, "count": 18},
    {"name": "Mylapore / Royapettah", "lat": 13.0339, "lon": 80.2687, "radius": 3.0, "count": 18},
    {"name": "Guindy / Saidapet", "lat": 13.0067, "lon": 80.2020, "radius": 3.0, "count": 16},
    {"name": "Tambaram / Chromepet", "lat": 12.9229, "lon": 80.1275, "radius": 4.0, "count": 18},
    {"name": "Porur / Ramapuram", "lat": 13.0382, "lon": 80.1565, "radius": 4.0, "count": 16},
    {"name": "OMR / Sholinganallur", "lat": 12.9010, "lon": 80.2279, "radius": 5.0, "count": 20},
    {"name": "Ambattur / Avadi", "lat": 13.1143, "lon": 80.1548, "radius": 4.0, "count": 15},
    {"name": "Koyambedu / Vadapalani", "lat": 13.0732, "lon": 80.1913, "radius": 3.0, "count": 15},
    {"name": "Nungambakkam / Kilpauk", "lat": 13.0626, "lon": 80.2407, "radius": 3.0, "count": 15},

    # Tamil Nadu Major Cities (~180 donors)
    {"name": "Coimbatore", "lat": 11.0168, "lon": 76.9558, "radius": 8.0, "count": 25},
    {"name": "Madurai", "lat": 9.9252, "lon": 78.1198, "radius": 8.0, "count": 22},
    {"name": "Tiruchirappalli (Trichy)", "lat": 10.7905, "lon": 78.7047, "radius": 8.0, "count": 20},
    {"name": "Salem", "lat": 11.6643, "lon": 78.1460, "radius": 8.0, "count": 18},
    {"name": "Tirunelveli", "lat": 8.7139, "lon": 77.7567, "radius": 8.0, "count": 15},
    {"name": "Vellore", "lat": 12.9165, "lon": 79.1325, "radius": 7.0, "count": 16},
    {"name": "Erode", "lat": 11.3410, "lon": 77.7172, "radius": 7.0, "count": 14},
    {"name": "Thanjavur", "lat": 10.7870, "lon": 79.1378, "radius": 7.0, "count": 12},
    {"name": "Kanchipuram", "lat": 12.8342, "lon": 79.7036, "radius": 6.0, "count": 14},
    {"name": "Cuddalore", "lat": 11.7480, "lon": 79.7714, "radius": 7.0, "count": 10},
    {"name": "Tiruppur", "lat": 11.1085, "lon": 77.3411, "radius": 7.0, "count": 12},
    {"name": "Hosur", "lat": 12.7409, "lon": 77.8253, "radius": 7.0, "count": 10},
]


def generate_donors():
    random.seed(2026)
    donors = []
    donor_idx = 1

    for cluster in CLUSTERS:
        lat0, lon0 = cluster["lat"], cluster["lon"]
        radius_km = cluster["radius"]

        for _ in range(cluster["count"]):
            if random.random() < 0.55:
                name = f"{random.choice(MALE_NAMES)} {random.choice(LAST_NAMES)}"
            else:
                name = f"{random.choice(FEMALE_NAMES)} {random.choice(LAST_NAMES)}"

            blood_group = random.choices(BLOOD_GROUPS, weights=BLOOD_PROBS)[0]
            age = random.randint(18, 62)

            # Random location offset within cluster radius
            dist = random.uniform(0.1, radius_km)
            angle = random.uniform(0, 2 * math.pi)
            lat = lat0 + (dist * math.cos(angle)) / 111.32
            lon = lon0 + (dist * math.sin(angle)) / (111.32 * math.cos(math.radians(lat0)))

            is_first_time = random.random() < 0.15
            days_since = None if is_first_time else random.randint(30, 500)
            past_donations = 0 if is_first_time else random.randint(1, 20)

            response_rate = 0.5 if is_first_time else round(random.uniform(0.40, 0.98), 2)
            avg_response_time = 30.0 if is_first_time else round(random.uniform(3.0, 75.0), 1)
            is_available = 1 if random.random() < 0.78 else 0

            avatar_img = f"https://i.pravatar.cc/100?img={(donor_idx % 70) + 1}"

            donors.append((
                name, blood_group, age, round(lat, 6), round(lon, 6),
                days_since, past_donations, response_rate, avg_response_time,
                is_available, avatar_img
            ))
            donor_idx += 1

    return donors


def seed_database():
    print(f"Connecting to database at {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)

    # Re-create tables if missing
    conn.execute("""
    CREATE TABLE IF NOT EXISTS donors (
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

    # Clear old minimal set and insert updated donor records
    conn.execute("DELETE FROM donors")

    donors = generate_donors()
    conn.executemany("""
    INSERT INTO donors (
        name, blood_group, age, latitude, longitude,
        days_since_last_donation, past_donations, response_rate,
        avg_response_time_min, is_available_now, image_url
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, donors)

    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM donors").fetchone()[0]
    conn.close()

    print(f"Successfully populated {count} donors across Tamil Nadu and Chennai!")


if __name__ == "__main__":
    seed_database()
