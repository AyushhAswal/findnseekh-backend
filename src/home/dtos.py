from typing import Any, Dict, List
from pydantic import BaseModel

from src.category.dtos import CategoryReadSchema
from src.locations.dtos import LocationSuggestionSchema
from src.skills.dtos import PopularSkillSchema
from src.teachers.dtos import TeacherCardSchema


class HomeOverviewSchema(BaseModel):
    """Aggregated payload for the Home page."""

    categories: List[CategoryReadSchema]
    popular_skills: List[PopularSkillSchema]
    locations: List[LocationSuggestionSchema]
    featured_teachers: List[TeacherCardSchema]
    stats: Dict[str, Any]

