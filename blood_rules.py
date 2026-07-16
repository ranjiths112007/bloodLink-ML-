"""
blood_rules.py
Hard medical compatibility rules for blood donation.
These are NEVER learned by ML - they are fixed medical facts.
"""

# recipient_blood_group -> list of donor blood groups that can donate to them
COMPATIBILITY = {
    "O-":  ["O-"],
    "O+":  ["O-", "O+"],
    "A-":  ["O-", "A-"],
    "A+":  ["O-", "O+", "A-", "A+"],
    "B-":  ["O-", "B-"],
    "B+":  ["O-", "O+", "B-", "B+"],
    "AB-": ["O-", "A-", "B-", "AB-"],
    "AB+": ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"],
}


def is_compatible(donor_blood_group: str, recipient_blood_group: str) -> bool:
    """Returns True if donor can legally/medically donate to recipient."""
    donor_blood_group = donor_blood_group.strip().upper()
    recipient_blood_group = recipient_blood_group.strip().upper()
    if recipient_blood_group not in COMPATIBILITY:
        raise ValueError(f"Unknown blood group: {recipient_blood_group}")
    return donor_blood_group in COMPATIBILITY[recipient_blood_group]


def is_eligible_by_recency(days_since_last_donation, min_gap_days=90):
    """
    Medical rule: donors must wait ~90 days (3 months) between whole blood donations.
    If days_since_last_donation is None, treat as first-time donor (eligible).
    """
    if days_since_last_donation is None:
        return True
    return days_since_last_donation >= min_gap_days


def is_eligible_by_age(age, min_age=18, max_age=65):
    return min_age <= age <= max_age
