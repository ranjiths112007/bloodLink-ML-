"""Safety-first donor screening helpers.

These are demo screening rules, not medical clearance. Final eligibility must
always be confirmed by an authorised blood bank or medical professional.
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

# Conservative demo thresholds. These MUST NOT be presented as medical clearance.
DEFAULT_MIN_AGE = 18
DEFAULT_MAX_AGE = 65
DEFAULT_MIN_GAP_DAYS = 90


def normalize_blood_group(value: str) -> str:
    value = str(value or "").strip().upper()
    if value not in VALID_BLOOD_GROUPS:
        raise ValueError(f"Unknown blood group: {value or '<empty>'}")
    return value


def is_compatible(donor_blood_group: str, recipient_blood_group: str) -> bool:
    donor = normalize_blood_group(donor_blood_group)
    recipient = normalize_blood_group(recipient_blood_group)
    return donor in COMPATIBILITY[recipient]


def is_eligible_by_recency(days_since_last_donation, min_gap_days: int = DEFAULT_MIN_GAP_DAYS) -> bool:
    if days_since_last_donation is None:
        return True
    try:
        days = float(days_since_last_donation)
    except (TypeError, ValueError):
        return False
    return days >= min_gap_days


def is_eligible_by_age(age, min_age: int = DEFAULT_MIN_AGE, max_age: int = DEFAULT_MAX_AGE) -> bool:
    try:
        age = int(age)
    except (TypeError, ValueError):
        return False
    return min_age <= age <= max_age


def screen_donor(donor: dict, recipient_blood_group: str, max_distance_km: float) -> tuple[bool, str]:
    """Return pass/fail plus a machine-readable screening reason."""
    try:
        recipient_blood_group = normalize_blood_group(recipient_blood_group)
    except ValueError:
        return False, "invalid_recipient_blood_group"
    if not is_compatible(donor.get("blood_group", ""), recipient_blood_group):
        return False, "blood_type_incompatible"
    if not is_eligible_by_age(donor.get("age")):
        return False, "age_out_of_range"
    if not is_eligible_by_recency(donor.get("days_since_last_donation")):
        return False, "too_soon_since_last_donation"
    try:
        distance = float(donor.get("distance_km", float("inf")))
    except (TypeError, ValueError):
        return False, "invalid_distance"
    if distance > max_distance_km:
        return False, "too_far"
    return True, "passed_demo_screening"
