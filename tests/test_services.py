from donor_service import availability_payload, validate_donor_profile
from role_api import ROLES, require_roles


def test_donor_profile_validation():
    assert validate_donor_profile({'blood_group':'o+','age':24}) == {'blood_group':'O+','age':24}


def test_invalid_donor_age():
    try:
        validate_donor_profile({'blood_group':'O+','age':17})
        assert False
    except ValueError:
        pass


def test_availability_is_boolean():
    result = availability_payload(1)
    assert result['is_available_now'] is True
    assert 'updated_at' in result


def test_roles_are_known():
    assert ROLES == {'donor','patient','hospital','admin'}
