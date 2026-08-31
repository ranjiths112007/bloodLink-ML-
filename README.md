<div align="center">

# 🩸 BloodLink

### Human-first AI-assisted blood donor matching

**Find the right donor when every minute matters.**

[![CI](https://github.com/ranjiths112007/bloodLink-ML-/actions/workflows/ci.yml/badge.svg)](https://github.com/ranjiths112007/bloodLink-ML-/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![scikit--learn](https://img.shields.io/badge/ML-scikit--learn-F7931E?logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Docker](https://img.shields.io/badge/Deploy-Docker-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

> **Safety notice:** BloodLink is a matching and prioritization prototype. It is not a medical diagnosis, medical clearance, or replacement for professional blood-bank screening. Final eligibility and compatibility decisions must be made by qualified healthcare professionals.

## What is BloodLink?

BloodLink is a full-stack AIML application for finding and prioritizing nearby blood-donor candidates for a blood request.

Instead of treating donor matching as a simple “same blood group + nearest location” search, BloodLink combines:

- deterministic blood-group compatibility rules
- application-level donor screening rules
- geographic distance
- donor availability
- historical response behaviour
- machine-learning response prediction
- explainable ranking reasons
- user authentication and roles
- persistent request and interaction data

The central design principle is:

```text
SAFETY RULES FIRST
        ↓
ELIGIBLE CANDIDATES
        ↓
ML PRIORITIZATION
        ↓
EXPLAINABLE RESULTS
        ↓
HUMAN DECISION
```

---

## Why it matters

During a blood request, the useful question is not simply:

> “Who is nearby?”

It is closer to:

> “Which compatible candidates can be considered, which are available, and which should be contacted first?”

BloodLink is designed to support that workflow while keeping the final medical decision outside the model.

---

## How it works

```text
User creates / explores a request
               ↓
       Request validation
               ↓
   Blood-group compatibility
               ↓
   Demo eligibility screening
               ↓
      Distance filtering
               ↓
        Eligible pool
               ↓
    ML response prediction
               ↓
    Operational ranking
               ↓
 Explainable donor shortlist
               ↓
    Human contact decision
               ↓
 Accepted / declined / no response / completed
               ↓
       Interaction history
               ↓
 Future model evaluation + retraining
```

The ML component never acts as the medical gatekeeper.

---

## Main user experiences

### Public matching experience

The public dashboard focuses on the fastest path to a useful result:

1. Select the required blood group.
2. Select urgency.
3. Select a search radius.
4. Select **Use my location**.
5. Grant browser location permission.
6. BloodLink calculates distance to donor records.
7. Compatible and screen-passing candidates are ranked.
8. Results show practical explanations for the ranking.

### Secure portal

The portal provides role-aware access for:

| Role | Main responsibility |
|---|---|
| **Donor** | Maintain donor details and availability; participate in requests |
| **Patient** | Create blood requests and review activity |
| **Hospital** | Create requests and record donor outcomes |
| **Admin** | Review operational metrics and request activity |

---

## Matching algorithm

BloodLink uses a hybrid **rules + ML ranking architecture**.

### 1. Request validation

The API validates:

- blood-group value
- latitude and longitude ranges
- search-radius limits
- urgency values
- JSON request structure

Invalid input is returned as a structured API error.

### 2. Compatibility screening

The project maintains a compatibility table for the eight blood-group labels used by the prototype:

```text
O-   O+
A-   A+
B-   B+
AB-  AB+
```

Only compatible donors move to the ranking stage.

This is an application-level screening rule and does not replace clinical crossmatching or blood-bank verification.

### 3. Application screening

The current prototype applies conservative demo constraints for:

- donor age
- donation recency
- distance
- blood compatibility

These values are product rules for the prototype, not universal medical policy.

### 4. Geographic distance

The backend calculates straight-line distance using the **Haversine formula**.

```text
Δlat = radians(lat₂ - lat₁)
Δlon = radians(lon₂ - lon₁)

a = sin²(Δlat / 2)
    + cos(lat₁) × cos(lat₂) × sin²(Δlon / 2)

c = 2 × atan2(√a, √(1-a))

d = R × c
```

where `R` is approximately `6371 km`.

### 5. ML response prediction

The current Random Forest model uses eight behavioural/context features:

| Feature | Purpose |
|---|---|
| `distance_km` | Distance from request |
| `days_since_last_donation` | Donation recency/history |
| `is_first_time_donor` | First-time vs returning donor signal |
| `age` | Donor profile feature |
| `past_donations` | Donation history |
| `response_rate` | Historical response behaviour |
| `avg_response_time_min` | Historical response speed |
| `is_available_now` | Current availability |

The model produces a response probability through `predict_proba()`.

### 6. Operational ranking

The prototype transforms the prediction and proximity into a transparent score:

```text
score = 85 × ML response probability
        + 15 × proximity contribution
```

The `85/15` weighting is an engineering heuristic for the prototype, not a statistically learned or clinically validated formula.

### 7. Explainability

Ranked candidates can include reasons such as:

```text
available_now
very_close
nearby
strong_response_history
fast_responder
high_predicted_response
```

The objective is to help a human understand the shortlist rather than presenting an unexplained number.

---

## Machine learning and data

### Development dataset

The repository includes a synthetic data generator that creates **6,000 donor/request interaction examples**.

The generated labels are based on manually designed behavioural assumptions plus random noise. This makes the dataset useful for development and reproducible demos, but it does **not** prove real-world predictive performance.

### Current model

The primary training script uses a `RandomForestClassifier` with:

- 400 trees
- maximum depth of 8
- minimum leaf size of 5
- balanced class weighting
- deterministic random seed

The training process records data-source information, metrics, feature importances and a model version.

### Real-data pathway

The repository also includes a real-data-ready training pipeline for an authorised historical outcome dataset.

The real-data path includes:

- required-column validation
- missing-value handling
- train/test splitting
- feature preprocessing
- Logistic Regression baseline
- ROC-AUC
- PR-AUC
- versioned model metadata

This allows future evaluation against genuine observed donor outcomes without pretending synthetic data is real evidence.

---

## ML feedback loop

Every donor interaction can become a future learning signal:

```text
Prediction
   ↓
Donor contacted
   ↓
Observed response
   ↓
Outcome stored
   ↓
Historical dataset
   ↓
Evaluate ranking quality
   ↓
Calibrate / retrain
   ↓
New model version
```

Useful future metrics include:

- ROC-AUC
- PR-AUC
- Precision@K
- Recall@K
- ranking quality such as NDCG@K
- calibration
- acceptance rate among top-ranked donors
- completion rate
- time to first accepted donor

---

## Location handling

BloodLink does not silently assume a user's location.

```text
Use my location
        ↓
Browser Geolocation API
        ↓
Permission prompt
        ↓
User approval
        ↓
Request coordinates
        ↓
Distance calculation
        ↓
Donor ranking
```

The public interface explains why location is needed and handles permission denial or unavailable location explicitly.

For donor privacy, exact donor coordinates are kept out of the public donor projection. The map uses a coarse location representation while distance remains available as a useful ranking signal.

---

## Data model

### Users

```text
user_id
email
password_hash
role
display_name
is_active
created_at
```

### Donors

```text
donor_id
name
blood_group
age
latitude
longitude
days_since_last_donation
past_donations
response_rate
avg_response_time_min
is_available_now
image_url
```

### Blood requests

```text
request_id
blood_group
latitude
longitude
max_distance_km
urgency
created_at
created_by
```

### Donor interactions

```text
interaction_id
request_id
donor_id
rank_position
predicted_probability
contacted_at
response
response_time_min
created_at
```

Supported outcomes:

```text
accepted
 declined
 no_response
 completed
```

---

## Authentication and roles

The current application supports:

```text
DONOR
PATIENT
HOSPITAL
ADMIN
```

The authentication layer provides:

- account registration
- login/logout
- session lookup
- password hashing
- protected routes
- role checks
- HTTP-only cookies
- SameSite cookie configuration
- secure-cookie configuration for production

Passwords are hashed using PBKDF2-HMAC-SHA256 rather than stored as plain text.

---

## API

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/health` | Backend, model and database health |
| `POST` | `/api/auth/register` | Create account |
| `POST` | `/api/auth/login` | Authenticate |
| `POST` | `/api/auth/logout` | End session |
| `GET` | `/api/auth/me` | Get current session |
| `POST` | `/api/match-donors` | Run donor matching |
| `POST` | `/api/requests` | Create protected blood request |
| `PUT` | `/api/donors/me` | Update donor profile/availability |
| `POST` | `/api/interactions` | Record donor outcome |
| `GET` | `/api/requests/<id>/interactions` | Request interaction history |
| `GET` | `/api/admin/metrics` | Admin operational metrics |
| `GET` | `/api/admin/requests` | Recent request activity |
| `GET` | `/api/admin/request-summary` | Request summary |

### Example request

```json
{
  "blood_group": "O+",
  "lat": 13.0827,
  "lon": 80.2707,
  "max_distance": 30,
  "urgency": "high"
}
```

### Example response fields

```json
{
  "request_id": 12,
  "screened_count": 43,
  "eligible_count": 5,
  "model_version": "synthetic-rf-…",
  "data_source": "synthetic",
  "matches": [],
  "excluded": [],
  "safety_notice": "..."
}
```

---

## Human-centered UI/UX

The interface is designed around the person's task rather than the technology behind it.

### Principles

**Clear next action** — the user should always know what to do next.

**Progressive disclosure** — technical information does not overwhelm the primary flow.

**Human language** — donors see useful context instead of ML jargon.

**Transparent location use** — the application explains why permission is required.

**Explainable recommendations** — ranked results provide reasons, not just scores.

**Responsive design** — layouts adapt to desktop and mobile screens.

**Explicit states** — loading, location unavailable, empty results and backend failures are represented visibly.

---

## Security and privacy

Current application safeguards include:

- PBKDF2 password hashing
- role-aware authorization
- HTTP-only sessions
- SameSite cookies
- production secure-cookie mode
- security response headers
- rate limiting for selected endpoints
- structured API errors
- privacy-safe donor map data
- repository exclusions for secrets and local databases

See [`SECURITY.md`](SECURITY.md) for the security and safety requirements.

A real deployment should additionally use audited authentication infrastructure, encrypted production storage, managed secrets, audit logs, verified institutional onboarding, explicit communication consent, vulnerability testing and appropriate legal/privacy/medical review.

---

## Notifications

The notification layer provides a provider-neutral interface for:

- SMS
- WhatsApp
- Email
- Push

Without a configured provider, the development implementation reports a queued state rather than falsely claiming that a message was delivered.

---

## Admin analytics

The application includes privacy-conscious aggregate operational metrics such as:

- request count
- urgency distribution
- blood-group demand
- contact count
- accepted contacts
- declined contacts
- no-response contacts
- completed outcomes
- acceptance rate
- completion rate
- mean predicted probability

---

## Testing and CI

The repository contains regression tests for:

- health and API responses
- invalid blood groups
- invalid coordinates
- authentication
- authorization boundaries
- password hashing
- donor validation
- workflow outcomes
- donor privacy projections
- notification behaviour

GitHub Actions is configured to install dependencies, compile Python sources and run the pytest suite for changes targeting `main`.

---

## Deployment

### Local

```bash
pip install -r requirements.txt
python train_model.py
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

### Docker

```bash
docker build -t bloodlink .
docker run -p 5000:5000 bloodlink
```

The container uses Gunicorn through the WSGI entrypoint.

### Production direction

```text
HTTPS
  ↓
Flask / Gunicorn
  ↓
Managed database
  ↓
ML model service/artifact
  ↓
Notification provider
  ↓
Monitoring + audit logs
```

SQLite is appropriate for the current prototype. A managed database is recommended for real multi-user deployments.

---

## Technology stack

| Layer | Technology |
|---|---|
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Backend | Python, Flask |
| Machine learning | scikit-learn |
| Primary model | Random Forest Classifier |
| Real-data baseline | Logistic Regression pipeline |
| Data processing | pandas, NumPy |
| Model serialization | joblib |
| Database | SQLite |
| Map | Leaflet + OpenStreetMap tiles |
| Authentication | Flask sessions + PBKDF2-HMAC-SHA256 |
| Testing | pytest |
| CI | GitHub Actions |
| Production server | Gunicorn |
| Containers | Docker / Docker Compose |

---

## Approximate source-language composition

GitHub Linguist may classify embedded CSS/JavaScript differently because much of the frontend is contained inside HTML files. The following is therefore an approximate repository composition rather than an official GitHub percentage:

| Language / format | Approx. share |
|---|---:|
| Python | **~65%** |
| HTML | **~25%** |
| JavaScript | **~6%** |
| CSS | **~3%** |
| SQL / config / Markdown | **~1%** |

Python dominates because it contains the backend, matching logic, authentication, data generation, training and supporting services.

---

## Project structure

```text
bloodLink-ML-/
├── app.py
├── matcher.py
├── blood_rules.py
├── train_model.py
├── ml_pipeline.py
├── generate_training_data.py
├── auth.py
├── auth_store.py
├── donor_service.py
├── workflow_service.py
├── notifications.py
├── privacy.py
├── app_hardening.py
├── admin_metrics.py
├── role_api.py
├── frontend_api.js
├── frontend_workflow.js
├── dashboard.html
├── portal.html
├── schema.sql
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── wsgi.py
├── tests/
├── .github/workflows/ci.yml
├── SECURITY.md
├── IMPLEMENTATION_STATUS.md
├── api_schema.md
└── LICENSE
```

---

## Project status

| Capability | Status |
|---|---|
| Full-stack web application | ✅ Implemented |
| Flask backend | ✅ Implemented |
| Donor matching | ✅ Implemented |
| Blood compatibility layer | ✅ Implemented |
| Browser geolocation | ✅ Implemented |
| ML ranking | ✅ Implemented |
| Explainable ranking | ✅ Implemented |
| Authentication | ✅ Implemented |
| Role-based access | ✅ Implemented |
| Persistent requests/interactions | ✅ Implemented |
| Admin metrics | ✅ Implemented |
| Privacy-safe donor projection | ✅ Implemented |
| Docker/Gunicorn deployment path | ✅ Implemented |
| Automated test/CI configuration | ✅ Implemented |
| Real donor dataset | ❌ Not included |
| Real-world ML validation | ❌ Not established |
| Clinical certification | ❌ Not claimed |
| Live communication provider | ⚙️ Requires provider configuration |

---

## Open-source license

BloodLink is released under the **MIT License**. See [`LICENSE`](LICENSE).

---

## Recognition / project credentials

This repository includes engineering-quality project markers such as automated CI, testing, documented architecture, model metadata, security documentation and an open-source license.

It does **not** claim medical certification, clinical approval, third-party validation, or any external award unless separately published and verifiable.

---

## Documentation

- [`SECURITY.md`](SECURITY.md) — security, privacy and safety requirements
- [`IMPLEMENTATION_STATUS.md`](IMPLEMENTATION_STATUS.md) — implementation boundaries
- [`api_schema.md`](api_schema.md) — API contract

---

<div align="center">

**BloodLink — technology for connecting the right donor candidate to the right request faster.**

</div>
