import os
import tempfile
import pytest


def test_password_hashing_round_trip():
    from auth import hash_password, verify_password
    encoded = hash_password("BloodLink-demo-123")
    assert verify_password("BloodLink-demo-123", encoded)
    assert not verify_password("wrong-password", encoded)


def test_password_minimum_length():
    from auth import hash_password
    with pytest.raises(ValueError):
        hash_password("short")


def test_blood_compatibility():
    from blood_rules import is_compatible
    assert is_compatible("O-", "AB+")
    assert is_compatible("A+", "A+")
    assert not is_compatible("B+", "A+")


def test_screening_recency_and_age():
    from blood_rules import is_eligible_by_recency, is_eligible_by_age
    assert is_eligible_by_recency(100)
    assert not is_eligible_by_recency(20)
    assert is_eligible_by_age(18)
    assert is_eligible_by_age(65)
    assert not is_eligible_by_age(17)
    assert not is_eligible_by_age(66)
