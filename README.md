# 🩸 BloodLink — Human-first AI Blood Donor Matching

BloodLink is an AI-assisted donor matching prototype that helps a patient or hospital find compatible, nearby donors and prioritize eligible candidates by predicted response likelihood.

> **Safety boundary:** BloodLink is a matching/recommendation system, not a medical diagnosis or final donor-eligibility authority. Final eligibility must be confirmed by an authorised blood bank or healthcare professional.

## What is implemented

- Blood-group compatibility screening before ML.
- Demo eligibility screening for age, donation recency and distance.
- Random Forest donor-response ranking.
- Explainable match reasons instead of score-only output.
- Persistent SQLite database — startup never deletes existing donor data.
- Blood-request creation and storage.
- Donor-contact/outcome logging for a future real-data feedback loop.
- API validation and structured errors.
- Health endpoint with model/data status.
- Responsive human-first dashboard with map, urgency, ranked matches and interaction logging.
- Fresh databases are automatically populated with clearly demo-only donor records; existing data is preserved.

## Architecture

```text
Patient / Hospital Request
          ↓
Request Validation
          ↓
Hard Safety Screening
(blood group + demo eligibility + distance)
          ↓
Eligible Donor Pool
          ↓
ML Response Ranking
          ↓
Operational Ranking + Explanation
          ↓
Top Donor Call List
          ↓
Contact / Response / Donation Outcome
          ↓
Historical Interaction Data
          ↓
Future Model Retraining
```

The ML model **never overrides the hard screening layer**.

## ML status

The repository includes a synthetic-data fallback so the demo works without private historical data. This is intentionally labelled as prototype data.

For real training, provide a CSV containing the required feature columns plus `label`, then run:

```bash
set BLOODLINK_DATA=path/to/real_interactions.csv
python train_model.py
```

On macOS/Linux:

```bash
BLOODLINK_DATA=path/to/real_interactions.csv python train_model.py
```

The training script records the data source, model version, ROC-AUC, PR-AUC and training timestamp. Synthetic metrics must **not** be interpreted as clinical validation or real-world performance.

## API

### `POST /api/match-donors`

```json
{
  "blood_group": "O+",
  "lat": 13.0827,
  "lon": 80.2707,
  "max_distance": 30,
  "urgency": "high"
}
```

Returns ranked matches, excluded candidates, screening counts, model version, safety notice and a persisted `request_id`.

### `POST /api/requests`

Creates a persistent blood request.

### `POST /api/interactions`

Logs a donor contact and its outcome (`accepted`, `declined`, `no_response`, or `completed`). These records form the basis for future real-world model training.

### `GET /api/requests/<request_id>/interactions`

Returns the interaction history for a request.

### `GET /api/health`

Returns service status, model version and record counts.

## Run locally

```bash
pip install -r requirements.txt
python train_model.py
python app.py
```

Open `http://127.0.0.1:5000`.

## Project structure

```text
app.py                    Flask API, persistence and workflow
matcher.py               Safety-first hybrid matching engine
blood_rules.py            Blood compatibility and screening rules
train_model.py            Model training/evaluation/versioning
generate_training_data.py Synthetic demo training data
dashboard.html            Human-first responsive product UI
bloodlink.html            Original showcase UI
requirements.txt          Python dependencies
tests/                    Regression tests
IMPLEMENTATION_STATUS.md  Implementation and safety notes
```

## Roadmap for real deployment

1. Replace demo donor data with consented, verified records.
2. Add authentication and role-based access for donors, patients, hospitals and admins.
3. Minimize donor location exposure and protect personal data.
4. Add real notification providers with consent and rate limiting.
5. Capture verified response and donation outcomes.
6. Retrain and calibrate the model on representative historical data.
7. Evaluate precision@K, recall@K, PR-AUC, calibration and real operational outcomes.
8. Add model monitoring, audit logs, migrations, backups and production deployment.

## Disclaimer

This project is an educational/research prototype. It should not be used to make autonomous medical eligibility decisions or to replace professional blood-bank screening.
