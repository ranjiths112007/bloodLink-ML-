"""Safety-first donor eligibility and blood-group compatibility rules.

IMPORTANT: These rules are screening rules for the demo. Final donor eligibility
must be confirmed by an authorised blood bank/medical professional.
"""

COMPATIBILITY = {
    "O-": ["O-"],
    "O+": ["O-", "O+"],
    "A-": ["O-", "A-"],
    "A+": ["O-", "O+", "A-", "A+"],
    "B-": ["O-", "B-"],
    "B+": ["O-", "O+", "B-", "B+"],
    "AB-": ["O-", "A-", "B-", "AB-"],
    "AB+": ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"],
}
VALID_BLOOD_GROUPS = frozenset(COMPATIBILITY)


def normalize_blood_group(value: str) -> str:
    value = str(value or "").strip().upper()
    if value not in VALID_BLOOD_GROUPS:
        raise ValueError(f"Unknown blood group: {value or '<empty>'}")
    return value


def is_compatible(donor_blood_group: str, recipient_blood_group: str) -> bool:
    donor = normalize_blood_group(donor_blood_group)
    recipient = normalize_blood_group(recipient_blood_group)
    return donor in COMPATIBILITY[recipient]


def is_eligible_by_recency(days_since_last_donation, min_gap_days: int = 90) -> bool:
    if days_since_last_donation is None:
        return True
    try:
        days = float(days_since_last_donation)
    except (TypeError, ValueError):
        return False
    return days >= min_gap_days


def is_eligible_by_age(age, min_age: int = 18, max_age: int = 65) -> bool:
    try:
        age = int(age)
    except (TypeError, ValueError):
        return False
    return min_age <= age <= max_age
