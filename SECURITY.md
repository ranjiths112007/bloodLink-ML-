# BloodLink Security & Safety

## Important
BloodLink is a prototype matching system. It is **not a medical diagnosis or medical clearance system**. Final donor eligibility must be confirmed by an authorised blood bank or medical professional.

## Privacy principles
- Do not expose exact donor coordinates to unauthenticated users.
- Collect only information needed for matching and communication.
- Obtain explicit consent before contacting a donor.
- Do not commit secrets, API keys, provider credentials, or private datasets.
- Keep production donor/contact data out of demo seed files.

## Production requirements before real deployment
1. Use a managed identity provider or thoroughly audited authentication service.
2. Enforce role-based authorization for donor, patient, hospital, and admin actions.
3. Encrypt sensitive data at rest and in transit.
4. Add audit logs for access to donor information.
5. Obtain appropriate legal, medical, privacy, and institutional approvals.
6. Use a verified notification provider with opt-in/opt-out handling.
7. Validate ML performance on representative, consented historical data before operational use.
8. Maintain model versions, training-data versions, evaluation metrics, and rollback procedures.
