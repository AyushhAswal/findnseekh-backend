from typing import Optional
from sqlalchemy.orm import Session
from fastapi import status

from src.locations.dtos import LocationSuggestionSchema
from src.profile.models import TeacherProfileModel
from src.skills.models import SkillListingModel
from src.utils.responses import ApiResponse

MAJOR_INDIAN_LOCATIONS = [
    {"city": "Delhi", "state": "NCT of Delhi", "display": "Delhi, NCT of Delhi"},
    {"city": "Bengaluru", "state": "Karnataka", "display": "Bengaluru, Karnataka"},
    {"city": "Mumbai", "state": "Maharashtra", "display": "Mumbai, Maharashtra"},
    {"city": "Pune", "state": "Maharashtra", "display": "Pune, Maharashtra"},
    {"city": "Dehradun", "state": "Uttarakhand", "display": "Dehradun, Uttarakhand"},
    {"city": "Noida", "state": "Uttar Pradesh", "display": "Noida, Uttar Pradesh"},
    {"city": "Gurugram", "state": "Haryana", "display": "Gurugram, Haryana"},
    {"city": "Lucknow", "state": "Uttar Pradesh", "display": "Lucknow, Uttar Pradesh"},
    {"city": "Hyderabad", "state": "Telangana", "display": "Hyderabad, Telangana"},
    {"city": "Chennai", "state": "Tamil Nadu", "display": "Chennai, Tamil Nadu"},
    {"city": "Kolkata", "state": "West Bengal", "display": "Kolkata, West Bengal"},
    {"city": "Jaipur", "state": "Rajasthan", "display": "Jaipur, Rajasthan"},
    {"city": "Chandigarh", "state": "Punjab & Haryana", "display": "Chandigarh"},
    {"city": "Ahmedabad", "state": "Gujarat", "display": "Ahmedabad, Gujarat"},
]


def get_location_suggestions(
    db: Session,
    query: Optional[str] = None,
    limit: int = 10,
) -> ApiResponse:
    """Get autocomplete suggestions for cities and states where teachers teach."""
    q_str = query.strip().lower() if query else ""

    # Gather distinct cities from TeacherProfileModel and SkillListingModel
    teacher_cities = (
        db.query(TeacherProfileModel.city, TeacherProfileModel.state)
        .filter(TeacherProfileModel.city.isnot(None))
        .distinct()
        .all()
    )

    results = []
    seen = set()

    for city, state in teacher_cities:
        if not city:
            continue
        c_clean = city.strip()
        s_clean = state.strip() if state else None
        display = f"{c_clean}, {s_clean}" if s_clean else c_clean
        if q_str and (q_str not in c_clean.lower() and (not s_clean or q_str not in s_clean.lower())):
            continue
        key = c_clean.lower()
        if key not in seen:
            seen.add(key)
            results.append(
                LocationSuggestionSchema(
                    city=c_clean,
                    state=s_clean,
                    display=display,
                    teacher_count=1,
                ).model_dump(mode="json")
            )

    # Supplement with major locations
    for loc in MAJOR_INDIAN_LOCATIONS:
        if len(results) >= limit:
            break
        key = loc["city"].lower()
        if key not in seen:
            if not q_str or (q_str in loc["city"].lower() or (loc["state"] and q_str in loc["state"].lower())):
                seen.add(key)
                results.append(
                    LocationSuggestionSchema(
                        city=loc["city"],
                        state=loc.get("state"),
                        display=loc["display"],
                        teacher_count=0,
                    ).model_dump(mode="json")
                )

    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Location suggestions fetched successfully",
        data=results[:limit],
    )

