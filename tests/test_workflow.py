from workflow_service import build_match_summary, prepare_donor_notifications, validate_outcome


def test_workflow_summary():
    result = build_match_summary({"request_id": 7, "matches": [{"donor_id": 1}], "model_version": "v1", "data_source": "synthetic"})
    assert result["request_id"] == 7
    assert result["matches_found"] == 1
    assert result["top_match"]["donor_id"] == 1


def test_only_available_matches_are_prepared_for_notification():
    matches = [
        {"donor_id": 1, "is_available_now": 1, "distance_km": 2},
        {"donor_id": 2, "is_available_now": 0, "distance_km": 3},
    ]
    notices = prepare_donor_notifications(matches, "O+", "critical")
    assert [n["donor_id"] for n in notices] == [1]
    assert notices[0]["notification_status"] == "requires_authenticated_consent"


def test_outcome_validation():
    assert validate_outcome(" ACCEPTED ") == "accepted"
    try:
        validate_outcome("unknown")
        assert False
    except ValueError:
        pass
