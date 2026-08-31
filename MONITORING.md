# BloodLink Production Monitoring

Track these metrics without exposing donor identity in dashboards:

- request volume and urgency distribution
- time from request to first accepted donor
- acceptance and completion rates
- ML ranking ROC-AUC / PR-AUC on authorised evaluation data
- model version used per request
- API latency and 4xx/5xx rates
- notification queue failures
- authentication failures and suspicious access patterns

Alert on service errors, abnormal authentication failures, notification-provider failures, and model-performance degradation. Do not log passwords, authentication cookies, exact donor coordinates, or private contact details.
