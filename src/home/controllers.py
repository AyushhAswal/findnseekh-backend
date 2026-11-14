from sqlalchemy.orm import Session
from fastapi import status

from src.category.controllers import list_categories
from src.home.dtos import HomeOverviewSchema
from src.locations.controllers import get_location_suggestions
from src.skills.controllers import get_popular_skills
from src.teachers.controllers import get_featured_teachers
from src.utils.responses import ApiResponse


def get_home_overview(db: Session) -> ApiResponse:
    """Aggregate all initial data needed to render the Home page in a single cached call."""
    categories_res = list_categories(db)
    popular_skills_res = get_popular_skills(db, limit=8)
    locations_res = get_location_suggestions(db, limit=8)
    featured_teachers_res = get_featured_teachers(db, limit=6)

    data = HomeOverviewSchema(
        categories=categories_res.data,
        popular_skills=popular_skills_res.data,
        locations=locations_res.data,
        featured_teachers=featured_teachers_res.data,
        stats={
            "total_teachers": "500+",
            "skills_offered": "50+",
            "cities_covered": "20+",
            "average_rating": 4.9,
        },
    ).model_dump(mode="json")

    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Home overview fetched successfully",
        data=data,
    )

