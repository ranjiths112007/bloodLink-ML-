# BloodLink API contract

## POST /api/match-donors
Request:
```json
{"blood_group":"O+","lat":13.08,"lon":80.27,"max_distance":30,"urgency":"high"}
```
Returns a persisted `request_id`, eligible ML-ranked matches, excluded candidates, model provenance, and a safety notice.

## POST /api/requests
Creates a persistent blood request without running matching.

## POST /api/interactions
Records an observed donor outcome (`accepted`, `declined`, `no_response`, or `completed`). This is the feedback source for future ML training.

## GET /api/requests/{request_id}/interactions
Returns the interaction history for a request.

## GET /api/health
Returns service, model, and database counters.

## Safety boundary
Matching is a recommendation layer. It does not diagnose, medically clear, or guarantee donor eligibility. Contact details and exact donor coordinates must remain behind authenticated consent workflows.
