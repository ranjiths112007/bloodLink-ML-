PRAGMA foreign_keys = ON;

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
);

CREATE TABLE IF NOT EXISTS blood_requests (
    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
    blood_group TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    max_distance_km REAL NOT NULL DEFAULT 30,
    urgency TEXT NOT NULL DEFAULT 'normal',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS donor_interactions (
    interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    donor_id INTEGER NOT NULL,
    rank_position INTEGER,
    predicted_probability REAL,
    contacted_at TEXT,
    response TEXT,
    response_time_min REAL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(request_id) REFERENCES blood_requests(request_id),
    FOREIGN KEY(donor_id) REFERENCES donors(donor_id)
);
