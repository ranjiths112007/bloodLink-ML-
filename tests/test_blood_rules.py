from blood_rules import is_compatible, is_eligible_by_age, is_eligible_by_recency, normalize_blood_group


def test_o_negative_is_compatible_with_o_positive():
    assert is_compatible('O-', 'O+')


def test_ab_positive_accepts_all_demo_groups():
    for donor in ('O-', 'O+', 'A-', 'A+', 'B-', 'B+', 'AB-', 'AB+'):
        assert is_compatible(donor, 'AB+')


def test_invalid_blood_group_rejected():
    try:
        normalize_blood_group('X+')
    except ValueError:
        pass
    else:
        raise AssertionError('invalid blood group should fail')


def test_age_boundary():
    assert is_eligible_by_age(18)
    assert is_eligible_by_age(65)
    assert not is_eligible_by_age(17)
    assert not is_eligible_by_age(66)


def test_donation_recency_boundary():
    assert not is_eligible_by_recency(89)
    assert is_eligible_by_recency(90)
    assert is_eligible_by_recency(None)
