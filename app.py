import math
import os
import random
import sqlite3
from functools import wraps
from flask import Flask, jsonify, request, send_file, session

from admin_metrics import summarize_interactions, summarize_requests
from auth_store import AuthStore
from blood_rules import VALID_BLOOD_GROUPS
from matcher import find_best_donors, MODEL_VERSION
from privacy import public_donor_view
from app_hardening import add_security_headers, rate_limit

app = Flask(__name__)
secret = os.environ.get("BLOODLINK_SECRET_KEY")
app.config["SECRET_KEY"] = secret or "dev-only-change-this-secret"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
if os.environ.get("BLOODLINK_ENV", "development") == "production":
    app.config["SESSION_COOKIE_SECURE"] = True
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("BLOODLINK_DATA_DIR", os.path.join(BASE_DIR, "data"))
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.environ.get("BLOODLINK_DB_PATH", os.path.join(DATA_DIR, "bloodlink.db"))
auth_store = None


@app.after_request
def security_headers(response):
    return add_security_headers(response)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def seed_demo_donors(conn):
    if conn.execute("SELECT COUNT(*) FROM donors").fetchone()[0] > 0:
        return
    try:
        from seed_tamilnadu_donors import generate_donors
        donors = generate_donors()
        conn.executemany("""
        INSERT INTO donors (
            name, blood_group, age, latitude, longitude,
            days_since_last_donation, past_donations, response_rate,
            avg_response_time_min, is_available_now, image_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, donors)
        conn.commit()
    except Exception as exc:
        print("Error seeding donors:", exc)



def init_db(seed_demo=True):
    global auth_store
    conn = get_db()
    conn.execute("CREATE TABLE IF NOT EXISTS donors (donor_id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,blood_group TEXT NOT NULL,age INTEGER NOT NULL,latitude REAL NOT NULL,longitude REAL NOT NULL,days_since_last_donation INTEGER,past_donations INTEGER DEFAULT 0,response_rate REAL DEFAULT 0.5,avg_response_time_min REAL DEFAULT 30.0,is_available_now INTEGER DEFAULT 0,image_url TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS blood_requests (request_id INTEGER PRIMARY KEY AUTOINCREMENT,blood_group TEXT NOT NULL,latitude REAL NOT NULL,longitude REAL NOT NULL,max_distance_km REAL NOT NULL DEFAULT 30,urgency TEXT NOT NULL DEFAULT 'normal',created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,created_by INTEGER)")
    conn.execute("CREATE TABLE IF NOT EXISTS donor_interactions (interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,request_id INTEGER NOT NULL,donor_id INTEGER NOT NULL,rank_position INTEGER,predicted_probability REAL,contacted_at TEXT,response TEXT CHECK(response IN ('accepted','declined','no_response','completed')),response_time_min REAL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(request_id) REFERENCES blood_requests(request_id),FOREIGN KEY(donor_id) REFERENCES donors(donor_id))")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_donors_blood_group ON donors(blood_group)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_interactions_request ON donor_interactions(request_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_interactions_donor ON donor_interactions(donor_id)")
    conn.commit(); conn.close()
    auth_store = AuthStore(DB_PATH)
    if seed_demo:
        conn = get_db(); seed_demo_donors(conn); conn.close()


def haversine_km(lat1, lon1, lat2, lon2):
    dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    return 6371.0 * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def error(message, code, status=400):
    return jsonify({"error":{"code":code,"message":message}}), status


def parse_location(payload):
    try: lat, lon, radius = float(payload["lat"]), float(payload["lon"]), float(payload.get("max_distance",30))
    except (KeyError, TypeError, ValueError): raise ValueError("Valid lat and lon are required.")
    if not (-90 <= lat <= 90 and -180 <= lon <= 180): raise ValueError("Latitude must be -90..90 and longitude -180..180.")
    if not (1 <= radius <= 500): raise ValueError("max_distance must be between 1 and 500 km.")
    return lat, lon, radius


def login_required(role=None):
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            user = session.get("user")
            if not user: return error("Authentication required.", "AUTH_REQUIRED", 401)
            if role and user.get("role") not in (role if isinstance(role, tuple) else (role,)): return error("You do not have permission for this action.", "FORBIDDEN", 403)
            return fn(*args, **kwargs)
        return wrapped
    return decorator


@app.route("/")
def index(): return send_file(os.path.join(BASE_DIR, "dashboard.html"))

@app.route("/portal")
def portal(): return send_file(os.path.join(BASE_DIR, "portal.html"))

@app.route("/api/auth/register", methods=["POST"])
@rate_limit
def register():
    payload=request.get_json(silent=True) or {}
    try: user=auth_store.register(payload.get("email"),payload.get("password"),payload.get("role"),payload.get("display_name"))
    except ValueError as exc: return error(str(exc),"REGISTRATION_FAILED")
    session.clear(); session["user"]=user; return jsonify({"user":user}),201

@app.route("/api/auth/login", methods=["POST"])
@rate_limit
def login():
    payload=request.get_json(silent=True) or {}
    user=auth_store.authenticate(payload.get("email"),payload.get("password"))
    if not user: return error("Invalid email or password.","INVALID_CREDENTIALS",401)
    session.clear(); session["user"]=user; return jsonify({"user":user})

@app.route("/api/auth/logout", methods=["POST"])
def logout(): session.clear(); return jsonify({"status":"logged_out"})

@app.route("/api/auth/me")
def me(): return jsonify({"user":session.get("user")})

@app.route("/api/health")
def health():
    try:
        conn=get_db(); counts=[conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in ("donors","blood_requests","donor_interactions")]; conn.close()
        return jsonify({"status":"ok","model_version":MODEL_VERSION,"donor_count":counts[0],"request_count":counts[1],"interaction_count":counts[2],"environment":os.environ.get("BLOODLINK_ENV","development")})
    except Exception:
        return jsonify({"status":"error","message":"service unavailable"}),503

@app.route("/api/match-donors", methods=["POST"])
@rate_limit
def match_donors():
    payload=request.get_json(silent=True)
    if not isinstance(payload,dict): return error("JSON request body is required.","INVALID_JSON")
    bg=str(payload.get("blood_group","")).strip().upper()
    if bg not in VALID_BLOOD_GROUPS: return error("Invalid blood group.","INVALID_BLOOD_GROUP")
    try: lat,lon,radius=parse_location(payload)
    except ValueError as exc: return error(str(exc),"INVALID_LOCATION")
    urgency=str(payload.get("urgency","normal")).lower()
    if urgency not in {"normal","high","critical"}: return error("Invalid urgency.","INVALID_URGENCY")
    conn=get_db(); rows=conn.execute("SELECT donor_id,name,blood_group,age,latitude,longitude,days_since_last_donation,past_donations,response_rate,avg_response_time_min,is_available_now,image_url FROM donors").fetchall(); conn.close()
    donors=[]
    for row in rows:
        d=dict(row); d["distance_km"]=round(haversine_km(lat,lon,d["latitude"],d["longitude"]),2); donors.append(d)
    top_n=int(payload.get("top_n", 200))
    try: result=find_best_donors({"blood_group":bg,"urgency":urgency},donors,top_n=top_n,max_distance_km=radius)
    except RuntimeError as exc: return error(str(exc),"MODEL_UNAVAILABLE",503)
    except ValueError as exc: return error(str(exc),"INVALID_REQUEST")
    conn=get_db(); cur=conn.execute("INSERT INTO blood_requests (blood_group,latitude,longitude,max_distance_km,urgency,created_by) VALUES (?,?,?,?,?,?)",(bg,lat,lon,radius,urgency,(session.get("user") or {}).get("user_id"))); result["request_id"]=cur.lastrowid; conn.commit(); conn.close()
    result["matches"]=[public_donor_view(d) for d in result["matches"]]
    return jsonify(result)

@app.route("/api/requests", methods=["POST"])
@login_required(("patient","hospital","admin"))
def create_request():
    payload=request.get_json(silent=True) or {}; bg=str(payload.get("blood_group","")).strip().upper()
    if bg not in VALID_BLOOD_GROUPS: return error("Invalid blood group.","INVALID_BLOOD_GROUP")
    try: lat,lon,radius=parse_location(payload)
    except ValueError as exc: return error(str(exc),"INVALID_LOCATION")
    urgency=str(payload.get("urgency","normal")).lower()
    if urgency not in {"normal","high","critical"}: return error("Invalid urgency.","INVALID_URGENCY")
    conn=get_db(); cur=conn.execute("INSERT INTO blood_requests (blood_group,latitude,longitude,max_distance_km,urgency,created_by) VALUES (?,?,?,?,?,?)",(bg,lat,lon,radius,urgency,session["user"]["user_id"])); rid=cur.lastrowid; conn.commit(); conn.close(); return jsonify({"request_id":rid,"status":"created"}),201

@app.route("/api/donors/me", methods=["PUT"])
@login_required("donor")
def update_donor_self():
    payload=request.get_json(silent=True) or {}; bg=str(payload.get("blood_group","")).strip().upper()
    try: age=int(payload.get("age")); available=1 if bool(payload.get("is_available_now")) else 0
    except (TypeError,ValueError): return error("age must be an integer","INVALID_DONOR_PROFILE")
    if bg not in VALID_BLOOD_GROUPS or not 18 <= age <= 65: return error("Invalid donor profile.","INVALID_DONOR_PROFILE")
    donor_id=payload.get("donor_id")
    if donor_id is None: return error("A verified donor_id link is required for this demo account.","DONOR_LINK_REQUIRED")
    try: donor_id=int(donor_id)
    except (TypeError,ValueError): return error("Invalid donor_id.","INVALID_DONOR_PROFILE")
    conn=get_db(); exists=conn.execute("SELECT donor_id FROM donors WHERE donor_id=?",(donor_id,)).fetchone()
    if not exists: conn.close(); return error("Donor not found.","DONOR_NOT_FOUND",404)
    conn.execute("UPDATE donors SET blood_group=?,age=?,is_available_now=? WHERE donor_id=?",(bg,age,available,donor_id)); conn.commit(); conn.close(); return jsonify({"status":"updated","available":bool(available)})

@app.route("/api/interactions", methods=["POST"])
@login_required(("donor","hospital","admin"))
def log_interaction():
    payload=request.get_json(silent=True) or {}
    try: donor_id=int(payload["donor_id"]); request_id=int(payload["request_id"]); predicted=max(0,min(1,float(payload.get("predicted_probability",0)))); rank=int(payload.get("rank_position",0))
    except (KeyError,TypeError,ValueError): return error("Invalid interaction payload.","INVALID_INTERACTION")
    outcome=str(payload.get("response","no_response")).lower()
    if outcome not in {"accepted","declined","no_response","completed"}: return error("Invalid response outcome.","INVALID_RESPONSE")
    conn=get_db();
    if not conn.execute("SELECT donor_id FROM donors WHERE donor_id=?",(donor_id,)).fetchone(): conn.close(); return error("Donor not found.","DONOR_NOT_FOUND",404)
    if not conn.execute("SELECT request_id FROM blood_requests WHERE request_id=?",(request_id,)).fetchone(): conn.close(); return error("Request not found.","REQUEST_NOT_FOUND",404)
    cur=conn.execute("INSERT INTO donor_interactions (request_id,donor_id,rank_position,predicted_probability,contacted_at,response,response_time_min) VALUES (?,?,?,?,CURRENT_TIMESTAMP,?,?)",(request_id,donor_id,rank,predicted,outcome,payload.get("response_time_min"))); iid=cur.lastrowid; conn.commit(); conn.close(); return jsonify({"interaction_id":iid,"request_id":request_id,"status":"logged"}),201

@app.route("/api/requests/<int:request_id>/interactions")
@login_required(("patient","hospital","admin"))
def request_interactions(request_id):
    conn=get_db(); rows=conn.execute("SELECT i.*,d.name,d.blood_group FROM donor_interactions i JOIN donors d ON d.donor_id=i.donor_id WHERE i.request_id=? ORDER BY i.created_at DESC",(request_id,)).fetchall(); conn.close(); return jsonify({"request_id":request_id,"interactions":[dict(r) for r in rows]})

@app.route("/api/admin/metrics")
@login_required("admin")
def admin_metrics():
    conn=get_db(); rows=[dict(r) for r in conn.execute("SELECT predicted_probability,response FROM donor_interactions").fetchall()]; conn.close(); return jsonify(summarize_interactions(rows))

@app.route("/api/admin/requests")
@login_required("admin")
def admin_requests():
    conn=get_db(); rows=[dict(r) for r in conn.execute("SELECT request_id,blood_group,urgency,max_distance_km,created_at FROM blood_requests ORDER BY request_id DESC LIMIT 100").fetchall()]; conn.close(); return jsonify({"requests":rows})

@app.route("/api/admin/request-summary")
@login_required("admin")
def admin_request_summary():
    conn=get_db(); rows=[dict(r) for r in conn.execute("SELECT blood_group,urgency FROM blood_requests").fetchall()]; conn.close(); return jsonify(summarize_requests(rows))

if __name__ == "__main__":
    init_db(seed_demo=True)
    app.run(host="127.0.0.1",port=int(os.getenv("PORT",5000)),debug=os.getenv("FLASK_DEBUG","0")=="1")
