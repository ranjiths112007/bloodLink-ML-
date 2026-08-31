from auth import hash_password, normalize_role, verify_password
from privacy import public_donor_view
from notifications import send_notification


def test_password_hash_round_trip():
    encoded = hash_password("correct-horse-battery")
    assert encoded != "correct-horse-battery"
    assert verify_password("correct-horse-battery", encoded)
    assert not verify_password("wrong-password", encoded)


def test_roles_are_strict():
    assert normalize_role(" DONOR ") == "donor"
    try:
        normalize_role("superuser")
        assert False
    except ValueError:
        pass


def test_public_donor_view_hides_coordinates():
    donor = {"donor_id": 1, "name": "A", "latitude": 13.0, "longitude": 80.0,
             "blood_group": "O+", "distance_km": 2.2}
    view = public_donor_view(donor)
    assert "latitude" not in view and "longitude" not in view
    assert view["distance_km"] == 2.2


def test_notification_never_fakes_delivery():
    result = send_notification("sms", "+910000000000", "test")
    assert result["status"] == "queued"
    assert result["provider_configured"] is False
