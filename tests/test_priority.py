
import pytest

from app.priority import (
    DEFAULT_WEIGHTS,
    calculate_priority_score,
    rank_bookings,
    validate_weights,
)


def test_default_weights_sum_to_one():
    assert sum(DEFAULT_WEIGHTS.values()) == pytest.approx(1.0)


def test_validate_default_weights():
    assert validate_weights(DEFAULT_WEIGHTS) is True


def test_calculate_priority_score():
    score = calculate_priority_score(75, 50, 50)
    assert score == 60.0


def test_calculate_priority_score_with_custom_weights():
    weights = {
        "urgency": 0.5,
        "availability": 0.3,
        "patient_history": 0.2,
    }
    score = calculate_priority_score(100, 50, 25, weights)
    assert score == 70.0

def test_reject_weights_that_do_not_sum_to_one():
    weights = {
        "urgency": 0.5,
        "availability": 0.5,
        "patient_history": 0.5,
    }
    with pytest.raises(ValueError):
        validate_weights(weights)


def test_reject_negative_priority_score():
    with pytest.raises(ValueError):
        calculate_priority_score(-10, 50, 50)


def test_reject_score_above_100():
    with pytest.raises(ValueError):
        calculate_priority_score(101, 50, 50)


def test_reject_invalid_urgency_weight():
    weights = {
        "urgency": -0.1,
        "availability": 0.5,
        "patient_history": 0.6,
    }
    with pytest.raises(ValueError):
        validate_weights(weights)


def test_higher_priority_booking_is_ranked_first():
    bookings = [
        {
            "booking_id": "B1",
            "priority_score": 40,
            "created_at": "2026-11-15T10:00:00",
        },
        {
            "booking_id": "B2",
            "priority_score": 80,
            "created_at": "2026-11-15T11:00:00",
        },
    ]

    ranked = rank_bookings(bookings)
    assert ranked[0]["booking_id"] == "B2"


def test_earlier_booking_wins_when_scores_are_equal():
    bookings = [
        {
            "booking_id": "B1",
            "priority_score": 70,
            "created_at": "2026-11-15T11:00:00",
        },
        {
            "booking_id": "B2",
            "priority_score": 70,
            "created_at": "2026-11-15T10:00:00",
        },
    ]

    ranked = rank_bookings(bookings)
    assert ranked[0]["booking_id"] == "B2"


def test_booking_id_breaks_remaining_ties():
    bookings = [
        {
            "booking_id": "B2",
            "priority_score": 70,
            "created_at": "2026-11-15T10:00:00",
        },
        {
            "booking_id": "B1",
            "priority_score": 70,
            "created_at": "2026-11-15T10:00:00",
        },
    ]

    ranked = rank_bookings(bookings)
    assert ranked[0]["booking_id"] == "B1"


def test_reject_invalid_booking_score():
    bookings = [
        {
            "booking_id": "B1",
            "priority_score": float("nan"),
            "created_at": "2026-11-15T10:00:00",
        }
    ]

    with pytest.raises(ValueError):
        rank_bookings(bookings)
