"""
Priority calculation and ranking for the medicine booking system.

Implements:
- Configurable priority weights
- Normalized factor scores (0-100)
- Deterministic weighted priority calculation
- Priority-based booking ranking
- Booking timestamp tie-breaking
"""

from datetime import datetime, timezone
from math import isclose, isfinite

# Provisional defaults from the companion workbook.
# Final weights must be approved by the project team.
DEFAULT_WEIGHTS = {
    "urgency": 0.4,
    "availability": 0.3,
    "patient_history": 0.3
}

FACTOR_NAMES = (
    "urgency",
    "availability",
    "patient_history"
)

def validate_weights(weights):
    """Validate priority weights and ensure they sum to 1."""

    if not isinstance(weights, dict):
        raise ValueError("Weights must be provided as a dictionary.")

    if set(weights) != set(FACTOR_NAMES):
        raise ValueError(
            "Weights must contain urgency, availability "
            "and patient_history."
        )

    for factor, weight in weights.items():
        if isinstance(weight, bool) or not isinstance(weight, (int, float)):
            raise ValueError(f"Invalid weight for {factor}.")

        if not isfinite(weight) or weight < 0 or weight > 1:
            raise ValueError(
                f"Weight for {factor} must be between 0 and 1."
            )

    total = sum(weights.values())

    if not isclose(total, 1.0, abs_tol=1e-9):
        raise ValueError("Priority weights must sum to 1.0.")

    return True

def calculate_priority_score(
    urgency_score,
    availability_score,
    patient_history_score,
    weights=None
):
    """
    Calculate a weighted priority score between 0 and 100.

    Each factor score must already be normalized to 0-100.
    Higher scores indicate higher priority.
    """

    if weights is None:
        weights = DEFAULT_WEIGHTS

    validate_weights(weights)

    scores = {
        "urgency": urgency_score,
        "availability": availability_score,
        "patient_history": patient_history_score
    }

    for factor, score in scores.items():
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise ValueError(f"Invalid score for {factor}.")

        if not isfinite(score) or not 0 <= score <= 100:
            raise ValueError(
                f"{factor} score must be between 0 and 100."
            )

    priority_score = sum(
        scores[factor] * weights[factor]
        for factor in FACTOR_NAMES
    )

    return round(priority_score, 2)

def _timestamp_key(created_at):
    """Convert a datetime or ISO timestamp into a UTC timestamp."""

    if isinstance(created_at, str):
        try:
            created_at = datetime.fromisoformat(
                created_at.replace("Z", "+00:00")
            )
        except ValueError as exc:
            raise ValueError("Invalid booking timestamp.") from exc

    if not isinstance(created_at, datetime):
        raise ValueError("created_at must be a datetime or ISO string.")

    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    return created_at.timestamp()

def rank_bookings(bookings):
    """
    Rank bookings by:
    1. Highest priority score first.
    2. Earliest booking timestamp first.
    3. Booking ID as a deterministic final tie-breaker.

    Each booking must contain:
    booking_id, priority_score and created_at.
    """

    for booking in bookings:
        if not all(
            key in booking
            for key in ("booking_id", "priority_score", "created_at")
        ):
            raise ValueError(
                "Each booking must contain booking_id, "
                "priority_score and created_at."
            )

        score = booking["priority_score"]

        if (
            isinstance(score, bool)
            or not isinstance(score, (int, float))
            or not isfinite(score)
        ):
            raise ValueError("Invalid booking priority score.")

    return sorted(
        bookings,
        key=lambda booking: (
            -booking["priority_score"],
            _timestamp_key(booking["created_at"]),
            str(booking["booking_id"])
        )
    )