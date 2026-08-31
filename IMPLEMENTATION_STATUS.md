# BloodLink implementation status

## Current state
BloodLink now contains a persistent SQLite-backed request and interaction workflow, role-aware session authentication, safety-first donor screening, ML response ranking, explainable match reasons, privacy-safe donor projections, notification abstraction, production container configuration, CI/test scaffolding, and a human-centered matching dashboard.

## Implemented
- Blood compatibility and conservative demo screening before ML ranking.
- Persistent donor, request, user, and donor-interaction storage.
- Session login/logout/register with donor/patient/hospital/admin roles.
- Protected request, interaction, and admin endpoints.
- Donor availability/profile update endpoint.
- Privacy-safe public donor views with coarse map coordinates.
- Rate limiting for high-risk public endpoints and baseline security headers.
- Admin request and interaction metrics.
- Real-data-ready ML training/evaluation script with ROC-AUC and PR-AUC.
- Production Docker/Gunicorn configuration.
- Frontend API/workflow helpers and integrated public dashboard.
- Automated regression tests and CI workflow configuration.
- Repository cleanup rules for local databases, caches, secrets, and virtual environments.

## Explicit production boundaries
The current model bundle remains a prototype model trained from synthetic/demo data. No real donor data, medical clearance, provider delivery, hospital verification, or production ML performance is claimed.

Before operational deployment, configure a managed identity provider or audited auth service, verified institutional/hospital onboarding, consented communication providers, encrypted production storage, appropriate privacy/legal/medical approvals, monitoring, and a representative authorised real-world outcome dataset.
