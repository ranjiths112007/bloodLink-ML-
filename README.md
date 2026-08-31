<div align="center">

# 🩸 BloodLink

### Human-first AI-assisted blood donor matching

**Find the right donor when every minute matters.**

[![BloodLink CI](https://github.com/ranjiths112007/bloodLink-ML-/actions/workflows/ci.yml/badge.svg)](https://github.com/ranjiths112007/bloodLink-ML-/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![scikit--learn](https://img.shields.io/badge/ML-scikit--learn-F7931E?logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Docker](https://img.shields.io/badge/Deploy-Docker-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

<p>
BloodLink is a full-stack AIML prototype that combines deterministic blood-group screening,
location-aware ranking, donor-response prediction, explainable recommendations,
role-based access, interaction tracking, and a human-centered interface.
</p>

</div>

> **Important safety boundary:** BloodLink is a matching and prioritization prototype. It is **not** a medical diagnosis, blood-bank clearance system, or substitute for clinical screening. Final donor eligibility must always be confirmed by an authorised blood bank or healthcare professional.

---

## ✨ Why BloodLink exists

Finding a donor is not just a “nearest person with the same blood group” problem. A useful matching system needs to answer several questions at once:

- Is the donor compatible with the requested blood group?
- Does the donor pass the application's screening rules?
- How far away is the donor from the request location?
- Is the donor available now?
- How likely is this donor to respond to a request?
- Can the system explain *why* one donor appears above another?
- Can the observed response become data for improving future models?

BloodLink is designed around that workflow.

```text
        HUMAN NEED
             │
             ▼
       Blood Request
             │
             ▼
    Request Validation
             │
             ▼
   ┌─────────────────────┐
   │ HARD SAFETY FILTER  │
   │ compatibility       │
   │ age / recency       │
   │ distance            │
   └──────────┬──────────┘
              │
              ▼
       Eligible Pool
              │
              ▼
      ML Response Model
              │
              ▼
    Operational Ranking
              │
              ▼
       Explainable List
              │
              ▼
       Human Contact
              │
       ┌──────┴──────┐
       ▼             ▼
   Accepted       Declined /
       │          No response
       ▼
  Donation outcome
       │
       ▼
 Historical data
       │
       ▼
 Future ML evaluation
```

The most important architectural rule is simple:

> **Rules decide who can enter the candidate pool. ML only helps decide who should be prioritised within that pool.**

---

## 🧭 Product experience

BloodLink has two connected experiences.

### 1. Public matching experience

The main dashboard is deliberately human-first:

1. Choose the required blood group.
2. Choose urgency.
3. Choose a search radius.
4. Click **Use my location**.
5. The browser asks for location permission.
6. BloodLink uses the approved coordinates to calculate request-to-donor distance.
7. Compatible and screen-passing donors are ranked.
8. The UI explains the reasons for the ranking.
9. Exact donor coordinates are not exposed publicly; the map receives a coarse location projection.

### 2. Secure portal

The `/portal` workspace supports role-aware flows for:

| Role | Purpose |
|---|---|
| **Donor** | Maintain donor information / availability and respond to requests |
| **Patient** | Create and track a blood request |
| **Hospital** | Create requests and record interaction outcomes |
| **Admin** | View operational metrics and request activity |

Authentication is session-based in the current prototype. Passwords are hashed with PBKDF2-HMAC-SHA256 rather than stored in plain text.

---

## 🧠 How the matching algorithm works

The matching engine in `matcher.py` is a **hybrid rule + ML ranking system**.

### Step 1 — Validate the request

The API validates:

- blood group ∈ `{O-, O+, A-, A+, B-, B+, AB-, AB+}`
- latitude ∈ `[-90, 90]`
- longitude ∈ `[-180, 180]`
- search radius ∈ `[1, 500] km`
- urgency ∈ `{normal, high, critical}`

Invalid inputs return structured API errors instead of raw server exceptions.

### Step 2 — Hard blood compatibility filter

The `blood_rules.py` compatibility table prevents incompatible blood groups from reaching the ML ranking stage.

Conceptually:

```text
Recipient O+  → O-, O+
Recipient A+  → O-, O+, A-, A+
Recipient B+  → O-, O+, B-, B+
Recipient AB+ → all listed ABO/Rh groups
```

This compatibility table is an application-level prototype rule. It does **not** replace blood-bank crossmatching, antibody screening, or medical clearance.

### Step 3 — Demo eligibility screening

Candidates are filtered by the current prototype rules:

- age: `18–65`
- donation gap: `>= 90 days` when a previous donation date is known
- distance: inside the request radius

These values are intentionally documented as **conservative demo rules**, not universal medical policy.

### Step 4 — Distance calculation

The backend computes geographic distance with the **Haversine formula**, which estimates great-circle distance from latitude/longitude coordinates.

```python
Δlat = radians(lat₂ - lat₁)
Δlon = radians(lon₂ - lon₁)

A = sin²(Δlat / 2)
    + cos(lat₁) × cos(lat₂) × sin²(Δlon / 2)

C = 2 × atan2(√A, √(1 - A))
D = R × C
```

where `R ≈ 6371 km`.

### Step 5 — ML response prediction

The current bundled model is a **Random Forest classifier** using eight features:

| Feature | Meaning | Why it matters |
|---|---|---|
| `distance_km` | Request-to-donor distance | Closer candidates are operationally easier to reach |
| `days_since_last_donation` | Donation recency | Helps represent recency constraints/history |
| `is_first_time_donor` | Whether there is no prior donation record | Separates first-time and returning patterns |
| `age` | Donor age | Used as a model signal, not a clinical decision |
| `past_donations` | Historical donation count | Approximate experience/engagement signal |
| `response_rate` | Historical response ratio | Strong behavioural signal |
| `avg_response_time_min` | Typical response delay | Helps prioritise faster responders |
| `is_available_now` | Current availability flag | Strong operational signal |

The model outputs `P(response = 1)` through `predict_proba()`.

### Step 6 — Operational ranking

The current prototype converts the ML probability to a 0–85 contribution and adds a 0–15 proximity contribution:

```text
compatibility_score
    = 85 × ML response probability
      + 15 × normalised proximity
```

The ranking is then sorted in descending score order.

This is intentionally simple and transparent. Those `85/15` weights are **engineering heuristics**, not statistically optimised weights.

### Step 7 — Human-readable explanations

The engine adds reasons such as:

```text
available_now
very_close
nearby
strong_response_history
fast_responder
high_predicted_response
```

So a user sees not just a number, but an understandable reason for the recommendation.

---

## 🤖 Machine learning: what is real and what is still prototype

This distinction is important.

### Current demo model

`generate_training_data.py` creates **6,000 synthetic donor/request interaction rows**. The label is produced from manually designed domain-style assumptions plus noise. `train_model.py` trains a `RandomForestClassifier` on that synthetic or supplied real CSV data.

Therefore:

> **The current model demonstrates the ML engineering pipeline. Its synthetic evaluation is not proof of real-world donor behaviour.**

The repository intentionally exposes the data source and model version so the UI/backend can distinguish synthetic prototype output from a future real model.

### Real-data path

There is also a `ml_pipeline.py` path designed for an authorised real dataset. It uses:

- schema validation
- missing-value imputation
- feature scaling
- Logistic Regression
- stratified train/test split
- ROC-AUC
- PR-AUC
- versioned output metadata

That gives BloodLink two useful development tracks:

```text
Synthetic data
    ↓
Demo / development / UI testing

Authorised real outcomes
    ↓
Model evaluation
    ↓
Calibration
    ↓
Operational validation
    ↓
Production candidate model
```

---

## 📊 Data model

The core SQLite database contains these logical entities:

### `users`

Identity and access information:

```text
user_id
email
password_hash
role
display_name
is_active
created_at
```

### `donors`

Matching-oriented donor profile data:

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

### `blood_requests`

A request submitted by a patient/hospital/admin or generated by the public demo flow:

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

### `donor_interactions`

The feedback-loop table:

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

Current response outcomes are:

```text
accepted
 declined
 no_response
 completed
```

This table is the bridge from a matching demo to a future behaviour-learning system.

---

## 🔄 The ML feedback loop

This is where BloodLink becomes more interesting than a static prediction demo.

```text
Request
   ↓
Model ranks donors
   ↓
Donor contacted
   ↓
Observed outcome
   ↓
Interaction stored
   ↓
Dataset grows
   ↓
Evaluate future model
   ↓
Retrain / calibrate
   ↓
Version new model
   ↓
Deploy only after validation
```

The project records the prediction alongside the observed outcome so later evaluation can answer questions such as:

- Are high-ranked donors actually responding more often?
- Is the model calibrated?
- Does ranking quality improve at `K=3`, `K=5`, or `K=10`?
- Is the model becoming biased toward a particular donor segment?
- Does urgency change operational performance?

---

## 📍 Location flow

Location is handled explicitly instead of pretending the application magically knows where the user is.

```text
User clicks "Use my location"
          ↓
Browser Geolocation API
          ↓
Browser permission prompt
          ↓
Approved coordinates
          ↓
BloodLink request location
          ↓
Haversine distance against donor records
          ↓
Distance-aware ranking
```

The application can still be explored without location permission, but **real nearby distance matching requires a real request location**.

Privacy is intentionally separated from matching:

- exact donor coordinates remain server-side
- public responses contain approximate map coordinates
- distance is still returned as a useful ranking signal
- future contact details should be released only through authenticated, consented workflows

---

## 🎨 UX and design philosophy

BloodLink is designed around a **human-first** rather than “AI-first” experience.

The main principles are:

### Explain, don't impress

Instead of showing only:

```text
Score: 91
```

the UI can explain:

```text
Available now
Very close
Strong response history
Fast responder
```

### Reduce cognitive load

The public flow uses a small number of decisions:

```text
Blood group → radius → urgency → location → results
```

### Show system state

The interface distinguishes states such as:

```text
Loading…
System online
Location not shared
Location ready
No compatible donors
API unavailable
```

### Design for mobile first behaviour

The dashboard collapses its multi-column layout on smaller screens and keeps the primary action readable.

### Don't expose technical jargon to donors

A donor should see:

> Someone nearby needs O+ blood.

not:

> Your predicted response probability is 0.83.

Model details belong primarily in technical/admin views.

---

## 🔐 Security and privacy

The repository includes a prototype security layer, but it should **not** be confused with a completed security audit.

Current protections include:

- PBKDF2-HMAC-SHA256 password hashing
- role-aware protected routes
- HTTP-only session cookies
- `SameSite=Lax` cookies
- secure cookies in production mode
- basic security headers
- rate limiting for selected public/high-risk endpoints
- structured API errors
- exact donor coordinates withheld from public projections
- `.gitignore` rules for local DBs, environments and secrets

The security requirements are documented separately in [`SECURITY.md`](SECURITY.md).

### Before real deployment

A real service would still require:

- a managed/audited identity provider or hardened auth service
- encrypted production storage
- strong secret management
- CSRF protection appropriate to the final auth architecture
- audit logging
- verified hospital onboarding
- explicit consent and communication preferences
- backup/restore procedures
- vulnerability scanning and penetration testing
- privacy/legal/medical review

---

## 📡 Notifications

`notifications.py` provides a provider-neutral notification abstraction for:

```text
SMS
WhatsApp
Email
Push
```

The current implementation **does not pretend messages were delivered**. In development it returns a queued state with `provider_configured: false` until a real provider is configured.

That is intentional: fake “success” is worse than an explicit integration boundary.

---

## 🏥 Admin analytics

The admin layer exposes privacy-conscious aggregate metrics such as:

- total contacts
- accepted contacts
- declined contacts
- no-response contacts
- completed outcomes
- acceptance rate
- completion rate
- mean predicted probability
- request counts by urgency
- request demand by blood group

The goal is to answer operational questions without turning the admin dashboard into a donor surveillance panel.

---

## 🌐 API reference

### `GET /api/health`

Returns backend/model health and record counters.

### `POST /api/auth/register`

Create a role-aware account.

### `POST /api/auth/login`

Authenticate an account and establish a session.

### `POST /api/auth/logout`

Clear the current session.

### `GET /api/auth/me`

Return the current authenticated user, if present.

### `POST /api/match-donors`

Run the hybrid matcher and persist the request.

Example:

```json
{
  "blood_group": "O+",
  "lat": 13.0827,
  "lon": 80.2707,
  "max_distance": 30,
  "urgency": "high"
}
```

Response contains, among other fields:

```json
{
  "request_id": 12,
  "matches": [],
  "excluded": [],
  "eligible_count": 5,
  "screened_count": 43,
  "model_version": "synthetic-rf-…",
  "data_source": "synthetic",
  "safety_notice": "…"
}
```

### `POST /api/requests`

Create a protected persistent request. Allowed roles: patient, hospital, admin.

### `POST /api/interactions`

Log an observed donor outcome. Allowed roles: donor, hospital, admin.

### `GET /api/requests/<request_id>/interactions`

View interaction history for an authenticated request owner class. Allowed roles: patient, hospital, admin.

### `PUT /api/donors/me`

Update the current donor profile/availability flow in the prototype. Allowed role: donor.

### `GET /api/admin/metrics`

Return aggregate interaction metrics. Allowed role: admin.

### `GET /api/admin/requests`

Return recent request records. Allowed role: admin.

### `GET /api/admin/request-summary`

Return aggregate request demand/urgency counts. Allowed role: admin.

A concise API contract is also available in [`api_schema.md`](api_schema.md).

---

## 🗂️ Repository structure

```text
bloodLink-ML-\
│
├── app.py                         # Flask API, DB, auth, requests, matching routes
├── wsgi.py                        # Gunicorn entrypoint + initialization
├── matcher.py                     # Hybrid safety-first ML ranking engine
├── blood_rules.py                 # Blood compatibility and screening helpers
│
├── train_model.py                 # Random Forest training/evaluation
├── generate_training_data.py      # Synthetic development dataset generator
├── ml_pipeline.py                # Real-data-ready alternate ML pipeline
├── donor_response_model.joblib    # Bundled demo model artifact
│
├── auth.py                        # Password hashing + role normalization
├── auth_store.py                  # SQLite-backed user store
├── role_api.py                    # Reusable role authorization helpers
├── donor_service.py               # Donor validation + availability helpers
├── workflow_service.py            # Request/notification workflow helpers
├── notifications.py               # Provider-neutral notifications boundary
├── privacy.py                     # Public donor data projection
├── admin_metrics.py               # Aggregate operational metrics
├── app_hardening.py               # Rate limiting + security headers
│
├── dashboard.html                 # Public human-first matching experience
├── portal.html                    # Authenticated role-aware workspace
├── frontend_api.js                # Browser API client
├── frontend_workflow.js           # Browser workflow helpers
├── bloodlink.html                 # Earlier showcase UI
│
├── schema.sql                     # Reference database schema
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Gunicorn production image
├── docker-compose.yml              # Local production-like container setup
├── .gitignore                     # Secrets/cache/database exclusions
│
├── .github/workflows/ci.yml       # Automated CI: syntax + pytest
├── tests/                          # Regression and route/service tests
├── SECURITY.md                     # Security/privacy boundaries
├── MONITORING.md                   # Monitoring recommendations
├── IMPLEMENTATION_STATUS.md       # Implementation boundary/status
└── api_schema.md                   # API contract
```

---

## 🛠️ Tech stack

| Layer | Technology | Role in BloodLink |
|---|---|---|
| UI | HTML5 | Structure and accessible product markup |
| UI styling | CSS3 | Responsive visual system and human-first presentation |
| Browser logic | JavaScript | Maps, location, forms and API interactions |
| Mapping | Leaflet + OpenStreetMap tiles | Request and coarse donor-area visualisation |
| Backend | Python + Flask | REST API, workflow, persistence and auth |
| Data processing | pandas + NumPy | Dataset handling and ML feature preparation |
| ML | scikit-learn | Random Forest + evaluation + alternate Logistic Regression pipeline |
| Model artifact | joblib | Serialised model bundle |
| Database | SQLite | Prototype persistence |
| Authentication | Flask sessions + PBKDF2-HMAC | Prototype role-aware account access |
| Runtime | Gunicorn | Production WSGI server |
| Packaging | Docker / Docker Compose | Reproducible runtime/deployment path |
| Testing | pytest | Python regression tests |
| CI | GitHub Actions | Automated syntax checking + test execution |

---

## 📈 Language usage

The following is an **approximate implementation-surface breakdown by tracked text-file size**, not an official GitHub Linguist measurement. CSS is embedded inside the HTML files, so it is counted under HTML here.

```text
HTML          ~52%   ██████████████████████████
Python        ~43%   ██████████████████████
JavaScript     ~2%   █
Markdown       ~2%   █
SQL/YAML/etc.  ~1%   ▏
```

### What those percentages mean

**HTML (~52%)** — Most of the user-facing experience lives in the two main web interfaces. They contain the visual system, responsive layout and embedded CSS.

**Python (~43%)** — This is the application/AI core: Flask routes, database handling, matching logic, blood rules, model training, authentication, privacy, notifications, workflow services and tests.

**JavaScript (~2%)** — Browser API calls and reusable workflow helpers. Much of the current UI behaviour is also embedded directly in the HTML applications.

**Markdown (~2%)** — Documentation, security notes, monitoring notes, API contract and implementation status.

**SQL/YAML/other (~1%)** — Reference schema and GitHub Actions/deployment configuration.

---

## 🧪 Testing strategy

The repository contains tests for several important boundaries:

```text
Authentication
    ↓
password hashing / login / duplicate users

Rules
    ↓
blood compatibility / age / donation recency

API
    ↓
health / invalid blood group / invalid location / protected routes

Privacy
    ↓
exact coordinates excluded from public projection

Notifications
    ↓
never claim delivery without a configured provider

Workflow
    ↓
match summaries / outcomes / availability filtering
```

CI runs on pushes to `main` and pull requests targeting `main` with:

```text
checkout
  ↓
Python 3.11
  ↓
pip install -r requirements.txt
  ↓
python -m compileall -q .
  ↓
pytest -q
```

---

## 🚀 Run locally

### Option A — Python

```bash
git clone https://github.com/ranjiths112007/bloodLink-ML-.git
cd bloodLink-ML-
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Train the demo model:

```bash
python train_model.py
```

Start the application:

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

Authenticated workspace:

```text
http://127.0.0.1:5000/portal
```

### Option B — Docker

```bash
docker compose up --build
```

The container uses Gunicorn through `wsgi.py` and persists the SQLite application data inside the Compose volume.

---

## ⚙️ Environment configuration

Common configuration variables include:

```text
BLOODLINK_ENV=development|production
BLOODLINK_SECRET_KEY=<strong-secret>
BLOODLINK_DATA_DIR=<application-data-directory>
BLOODLINK_DB_PATH=<optional-db-path>
BLOODLINK_DATA=<optional-real-training-csv>
BLOODLINK_REAL_DATA_PATH=<alternate-authorised-training-csv>
BLOODLINK_RATE_WINDOW_SECONDS=60
BLOODLINK_RATE_LIMIT=120
PORT=5000
FLASK_DEBUG=0
```

For production, **never use the fallback development secret**. Supply a strong secret through a proper secret-management system.

---

## 🧠 Training with authorised real data

The current primary training script expects the same feature columns plus a binary `label`:

```text
 distance_km
 days_since_last_donation
 is_first_time_donor
 age
 past_donations
 response_rate
 avg_response_time_min
 is_available_now
 label
```

Then:

Windows PowerShell / CMD:

```powershell
set BLOODLINK_DATA=path\to\authorised_interactions.csv
python train_model.py
```

macOS/Linux:

```bash
BLOODLINK_DATA=path/to/authorised_interactions.csv python train_model.py
```

The alternate `ml_pipeline.py` expects `responded` instead of `label` and uses a preprocessing + Logistic Regression pipeline.

### Do not use private medical data casually

Any real donor dataset must be:

- lawfully collected and authorised for this use
- appropriately consented or otherwise approved
- minimised to necessary fields
- access-controlled
- securely stored
- reviewed for privacy/medical/legal requirements

---

## 🧮 Evaluation metrics

The project already records:

- ROC-AUC
- PR-AUC
- classification report
- model/data source
- model version
- training timestamp
- feature importances for the Random Forest path

For a real production model, add:

```text
Precision@K
Recall@K
NDCG@K
Brier score
Calibration curves
Response rate by rank position
Time-to-accept
Donation completion rate
Model drift
Data drift
```

For BloodLink, ranking metrics and operational outcomes are often more informative than a single generic accuracy number.

---

## 📦 Model artifact

`donor_response_model.joblib` is a serialised demo model bundle. The bundle contains:

```text
model
features
model_version
data_source
metrics
```

The exact current model artifact should be treated as a **demo dependency**, not a validated medical model.

---

## 🧩 Design decisions worth knowing

### Why rules before ML?

Because an ML model is not the right place to encode hard safety constraints. A predictive model should not be able to “score” its way around a compatibility rule.

### Why Random Forest?

It is a practical baseline for tabular features, supports probability estimates and feature importance, and is easy to explain in a student/portfolio context.

It is not claimed to be the best possible model for this problem.

### Why SQLite?

It keeps the prototype simple, local and easy to run. A larger deployment would likely move to PostgreSQL or another managed relational store.

### Why coarse donor coordinates?

A donor's exact home/location is sensitive information. The application can still calculate distance internally while reducing unnecessary public exposure.

### Why synthetic data?

The project needs a working demonstration without exposing real donor data. Synthetic data is acceptable for prototyping the pipeline; it is not a substitute for real validation.

---

## 🗺️ Production architecture target

The current repository is a strong prototype foundation. A larger deployment could evolve into:

```text
                 ┌─────────────────────┐
                 │ Web / Mobile Client │
                 └──────────┬──────────┘
                            │ HTTPS
                            ▼
                  ┌─────────────────┐
                  │ API / Auth Layer │
                  └────────┬────────┘
                           │
           ┌───────────────┼────────────────┐
           ▼               ▼                ▼
      Request Service   Match Service   Notification Worker
           │               │                │
           ▼               ▼                ▼
      PostgreSQL       ML Model Store    SMS / WhatsApp / Email
           │               │
           └───────┬───────┘
                   ▼
             Outcome Events
                   │
                   ▼
            ML Evaluation / MLOps
```

For scale, the likely evolution is:

```text
SQLite → PostgreSQL
in-process rate limit → Redis / gateway limit
local sessions → managed identity provider
local notifications → verified provider
manual retraining → scheduled model pipeline
basic logs → central observability
```

---

## ✅ Current implementation checklist

| Capability | Status |
|---|---|
| Human-centered UI | ✅ |
| Responsive dashboard | ✅ |
| Browser location permission flow | ✅ |
| Coarse donor-map privacy | ✅ |
| Blood compatibility rules | ✅ |
| Donor screening layer | ✅ |
| Haversine distance | ✅ |
| ML response ranking | ✅ |
| Explainable match reasons | ✅ |
| Persistent SQLite data | ✅ |
| Authentication | ✅ Prototype |
| Role-based access | ✅ Prototype |
| Donor availability | ✅ Prototype |
| Interaction/outcome logging | ✅ |
| Admin aggregate metrics | ✅ |
| Notification abstraction | ✅ |
| Rate limiting | ✅ Basic |
| Security headers | ✅ Baseline |
| Docker deployment | ✅ |
| Gunicorn WSGI path | ✅ |
| Automated tests | ✅ |
| GitHub Actions CI | ✅ |
| Real-data-ready ML path | ✅ |
| Real donor dataset | ❌ Not included |
| Medical validation | ❌ Not included |
| Verified hospitals | ❌ Not included |
| Real notification provider | ❌ Not configured |
| Production security audit | ❌ Not completed |

---

## 🔮 Future roadmap

### Near term

- Better donor-to-user identity linking
- Fully connected donor response UI
- richer patient/hospital request history
- stronger audit/event logging
- database migrations
- better automated end-to-end browser tests

### ML evolution

```text
Synthetic baseline
      ↓
Authorised historical data
      ↓
Calibration
      ↓
Ranking evaluation
      ↓
Bias / drift checks
      ↓
Champion vs challenger models
      ↓
Controlled deployment
```

### Product evolution

```text
One request
   ↓
Multiple donor contacts
   ↓
Consent-aware notifications
   ↓
Hospital confirmation
   ↓
Completion tracking
   ↓
Real outcome analytics
   ↓
Demand forecasting
```

A future demand model could also estimate blood-group demand by region/time and help institutions prepare for recurring shortages.

---

## 📚 Important documentation

- [`SECURITY.md`](SECURITY.md) — security, privacy and medical-safety boundaries
- [`MONITORING.md`](MONITORING.md) — monitoring recommendations
- [`IMPLEMENTATION_STATUS.md`](IMPLEMENTATION_STATUS.md) — implementation boundary/status
- [`api_schema.md`](api_schema.md) — API contract
- [`schema.sql`](schema.sql) — reference database schema

---

## 🧑‍💻 Why this is a strong AIML project

BloodLink is more than a classifier notebook. It demonstrates a complete engineering loop:

```text
Problem definition
      ↓
Data representation
      ↓
Domain rules
      ↓
Machine learning
      ↓
Backend API
      ↓
Database
      ↓
Frontend UX
      ↓
Authentication
      ↓
Privacy boundaries
      ↓
Testing / CI
      ↓
Deployment path
      ↓
Future feedback loop
```

That combination is the real value of the project: **AI is one component inside a usable system, not the entire product.**

---

## ⚠️ Limitations you should know before presenting this project

Be transparent when demonstrating BloodLink:

1. The bundled model is trained with synthetic/demo data.
2. The model's synthetic ROC-AUC/PR-AUC must not be described as clinical or real-world validation.
3. The donor profiles are demo records, not a live donor registry.
4. Notification channels are an integration boundary until a real provider is configured.
5. Application-level screening rules are not medical clearance.
6. The current authentication implementation is suitable for a prototype, not a completed security audit.
7. Exact operational deployment requires appropriate institutional, medical, privacy and legal review.

Being explicit about these limits makes the engineering story stronger, not weaker.

---

## 📄 License

Add the license that matches how you want BloodLink to be reused. A license file is intentionally not invented here.

---

<div align="center">

### Built as a human-first AIML systems project 🩸

**BloodLink — technology should help people act faster, not make decisions for them.**

</div>
