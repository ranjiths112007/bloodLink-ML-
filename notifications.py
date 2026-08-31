"""Notification abstraction.

Providers are intentionally not hard-coded. Configure an SMS/WhatsApp/push
provider behind this interface after obtaining the required credentials,
consent, and local regulatory approvals.
"""
import logging

logger = logging.getLogger(__name__)


def send_notification(channel: str, destination: str, message: str) -> dict:
    channel = str(channel or "").lower()
    if channel not in {"sms", "whatsapp", "email", "push"}:
        raise ValueError("Unsupported notification channel")
    if not destination or not message:
        raise ValueError("destination and message are required")
    # Safe development behavior: never pretend a provider delivered a message.
    logger.info("Notification queued channel=%s destination=%s", channel, destination)
    return {"status": "queued", "channel": channel, "provider_configured": False}


def donor_match_message(blood_group: str, urgency: str, approximate_distance_km: float) -> str:
    urgency_label = str(urgency).capitalize()
    return (f"BloodLink {urgency_label} request: someone nearby needs {blood_group} blood. "
            f"Approximate distance: {approximate_distance_km:.1f} km. "
            "Please respond only if you are willing and medically eligible to donate.")
