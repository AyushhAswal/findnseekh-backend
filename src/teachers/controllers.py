from decimal import Decimal
from typing import List, Optional
from sqlalchemy import func, or_, and_
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.category.models import CategoryModel
from src.profile.models import TeacherProfileModel
from src.skills.models import SkillListingModel
from src.teachers.dtos import TeacherCardSchema, TeacherPaginationSchema
from src.users.models import UserModel
from src.utils.responses import ApiResponse

SAMPLE_FEATURED_TEACHERS = [
    {
        "id": 101,
        "user_id": 101,
        "name": "Rohan Mehta",
        "specialty": "Guitar & Music Production",
        "rating": 4.8,
        "reviews_count": 18,
        "experience_years": 7,
        "city": "Delhi",
        "state": "NCT of Delhi",
        "location": "Delhi, NCT of Delhi",
        "teaching_mode": "both",
        "hourly_rate": Decimal("650.00"),
        "currency": "INR",
        "price_unit": "hour",
        "skills": ["Guitar", "Ableton", "Songwriting"],
        "avatar": None,
        "is_verified": True,
        "is_new": True,
        "bio": "Learn chords, fingerstyle and how to record your first song at home.",
    },
    {
        "id": 102,
        "user_id": 102,
        "name": "Vikram Aditya",
        "specialty": "Tabla & Indian Rhythm Systems",
        "rating": 4.8,
        "reviews_count": 39,
        "experience_years": 12,
        "city": "Lucknow",
        "state": "Uttar Pradesh",
        "location": "Lucknow, Uttar Pradesh",
        "teaching_mode": "offline",
        "hourly_rate": Decimal("600.00"),
        "currency": "INR",
        "price_unit": "hour",
        "skills": ["Tabla", "Rhythm", "Percussion"],
        "avatar": None,
        "is_verified": True,
        "is_new": False,
        "bio": "Delhi and Farrukhabad gharana exponent. TeenTaal, kaidas and stage accompaniment.",
    },
    {
        "id": 103,
        "user_id": 103,
        "name": "Kavya Nair",
        "specialty": "Kathak & Contemporary Dance",
        "rating": 4.9,
        "reviews_count": 41,
        "experience_years": 11,
        "city": "Noida",
        "state": "Uttar Pradesh",
        "location": "Noida, Uttar Pradesh",
        "teaching_mode": "offline",
        "hourly_rate": Decimal("800.00"),
        "currency": "INR",
        "price_unit": "hour",
        "skills": ["Kathak", "Contemporary", "Stage"],
        "avatar": None,
        "is_verified": True,
        "is_new": False,
        "bio": "Eleven years on stage. Technique, expression and performance prep for all ages.",
    },
    {
        "id": 104,
        "user_id": 104,
        "name": "Ananya Verma",
        "specialty": "Hindustani Classical Vocals",
        "rating": 4.8,
        "reviews_count": 64,
        "experience_years": 9,
        "city": "Dehradun",
        "state": "Uttarakhand",
        "location": "Dehradun, Uttarakhand",
        "teaching_mode": "both",
        "hourly_rate": Decimal("700.00"),
        "currency": "INR",
        "price_unit": "hour",
        "skills": ["Vocals", "Raga", "Harmonium"],
        "avatar": None,
        "is_verified": True,
        "is_new": False,
        "bio": "Trained in the Kirana gharana. Gentle, structured lessons for beginners and exam students.",
    },
    {
        "id": 105,
        "user_id": 105,
        "name": "Arjun Rao",
        "specialty": "Portrait & Street Photography",
        "rating": 4.9,
        "reviews_count": 52,
        "experience_years": 8,
        "city": "Bengaluru",
        "state": "Karnataka",
        "location": "Bengaluru, Karnataka",
        "teaching_mode": "both",
        "hourly_rate": Decimal("850.00"),
        "currency": "INR",
        "price_unit": "hour",
        "skills": ["Portrait", "Lightroom", "Composition"],
        "avatar": None,
        "is_verified": True,
        "is_new": False,
        "bio": "Master camera exposure, lighting gear, framing and editorial Lightroom grading.",
    },
    {
        "id": 106,
        "user_id": 106,
        "name": "Meera Sengupta",
        "specialty": "Clay Pottery & Terracotta",
        "rating": 4.7,
        "reviews_count": 28,
        "experience_years": 10,
        "city": "Kolkata",
        "state": "West Bengal",
        "location": "Kolkata, West Bengal",
        "teaching_mode": "offline",
        "hourly_rate": Decimal("550.00"),
        "currency": "INR",
        "price_unit": "hour",
        "skills": ["Pottery", "Wheel Work", "Glazing"],
        "avatar": None,
        "is_verified": True,
        "is_new": False,
        "bio": "Hand-building, wheel centering, terracotta firing and decorative glazing studio sessions.",
    },
]


def _build_teacher_card(db: Session, profile: TeacherProfileModel) -> TeacherCardSchema:
    user = db.query(UserModel).filter(UserModel.id == profile.user_id).first()
    user_name = user.name if user else "Teacher"

    # Get skill listings for this teacher to find rate and primary specialty
    listings = (
        db.query(SkillListingModel)
        .filter(SkillListingModel.teacher_id == profile.user_id, SkillListingModel.status == "published")
        .all()
    )

    hourly_rate = Decimal("500.00")
    specialty = profile.qualification or (profile.skills[0] if profile.skills else "Teacher")
    skills_list = list(profile.skills) if profile.skills else []

    if listings:
        prices = [listing.price_amount for listing in listings if listing.price_amount > 0]
        if prices:
            hourly_rate = min(prices)
        if not specialty or specialty == "Teacher":
            specialty = listings[0].title
        for listing in listings:
            if listing.title not in skills_list:
                skills_list.append(listing.title)

    city = profile.city
    state = profile.state
    location_parts = [p for p in (city, state) if p]
    location = ", ".join(location_parts) if location_parts else "Location Flexible"

    return TeacherCardSchema(
        id=profile.id,
        user_id=profile.user_id,
        name=user_name,
        specialty=specialty,
        rating=4.9,
        reviews_count=16,
        experience_years=profile.experience_years or 1,
        city=city,
        state=state,
        location=location,
        teaching_mode=profile.teaching_mode or "both",
        hourly_rate=hourly_rate,
        currency="INR",
        price_unit="hour",
        skills=skills_list[:4],
        avatar=None,
        is_verified=profile.is_verified,
        is_new=False,
        bio=profile.bio,
    )


def get_featured_teachers(
    db: Session,
    limit: int = 6,
    category: Optional[str] = None,
) -> ApiResponse:
    """Get featured teachers, sorted by rating/verification."""
    query = (
        db.query(TeacherProfileModel)
        .join(UserModel, UserModel.id == TeacherProfileModel.user_id)
        .filter(UserModel.is_active == True)  # noqa: E712
    )

    if category:
        cat = (
            db.query(CategoryModel)
            .filter(
                or_(
                    CategoryModel.slug == category.lower(),
                    CategoryModel.name.ilike(f"%{category}%"),
                )
            )
            .first()
        )
        if cat:
            query = query.filter(
                TeacherProfileModel.user_id.in_(
                    db.query(SkillListingModel.teacher_id)
                    .filter(
                        SkillListingModel.category_id == cat.id,
                        SkillListingModel.status == "published",
                    )
                )
            )

    profiles = query.limit(limit).all()

    cards: List[TeacherCardSchema] = []
    seen_ids = set()

    for p in profiles:
        card = _build_teacher_card(db, p)
        seen_ids.add(card.user_id)
        cards.append(card)

    # If database has fewer teachers than limit, fill with curated sample teachers
    if len(cards) < limit:
        for sample in SAMPLE_FEATURED_TEACHERS:
            if len(cards) >= limit:
                break
            if sample["user_id"] not in seen_ids:
                if category:
                    cat_lower = category.lower()
                    matches_cat = any(cat_lower in s.lower() for s in sample["skills"]) or cat_lower in sample["specialty"].lower()
                    if not matches_cat:
                        continue
                seen_ids.add(sample["user_id"])
                cards.append(TeacherCardSchema(**sample))

    data = [c.model_dump(mode="json") for c in cards]
    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Featured teachers fetched successfully",
        data=data,
    )


def list_teachers(
    db: Session,
    q: Optional[str] = None,
    category: Optional[str] = None,
    category_id: Optional[int] = None,
    city: Optional[str] = None,
    mode: Optional[str] = None,
    min_exp: Optional[int] = None,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    min_rating: Optional[float] = None,
    sort: Optional[str] = "recommended",
    page: int = 1,
    page_size: int = 12,
) -> ApiResponse:
    """List and filter teachers with sorting and pagination."""
    # Subquery to calculate minimum published listing price per teacher
    min_price_subq = (
        db.query(
            SkillListingModel.teacher_id,
            func.min(SkillListingModel.price_amount).label("min_listing_price"),
        )
        .filter(SkillListingModel.status == "published")
        .group_by(SkillListingModel.teacher_id)
        .subquery()
    )

    effective_price = func.coalesce(min_price_subq.c.min_listing_price, Decimal("500.00"))

    query = (
        db.query(TeacherProfileModel)
        .join(UserModel, UserModel.id == TeacherProfileModel.user_id)
        .outerjoin(min_price_subq, min_price_subq.c.teacher_id == TeacherProfileModel.user_id)
        .filter(UserModel.is_active == True)  # noqa: E712
    )

    if q:
        q_str = f"%{q.strip()}%"
        query = query.filter(
            or_(
                UserModel.name.ilike(q_str),
                TeacherProfileModel.bio.ilike(q_str),
                TeacherProfileModel.qualification.ilike(q_str),
            )
        )

    if city:
        query = query.filter(TeacherProfileModel.city.ilike(f"%{city.strip()}%"))

    if mode:
        if mode in ("online", "offline"):
            query = query.filter(
                or_(
                    TeacherProfileModel.teaching_mode == mode,
                    TeacherProfileModel.teaching_mode == "both",
                )
            )

    if min_exp is not None:
        query = query.filter(TeacherProfileModel.experience_years >= min_exp)

    if min_price is not None:
        query = query.filter(effective_price >= min_price)

    if max_price is not None:
        query = query.filter(effective_price <= max_price)

    if min_rating is not None and min_rating > 4.9:
        # Default unreviewed profile rating is 4.9
        query = query.filter(False)

    target_category_id = category_id
    if target_category_id is None and category:
        cat = (
            db.query(CategoryModel)
            .filter(
                or_(
                    CategoryModel.slug == category.lower(),
                    CategoryModel.name.ilike(f"%{category}%"),
                )
            )
            .first()
        )
        if cat:
            target_category_id = cat.id

    if target_category_id is not None:
        query = query.filter(
            TeacherProfileModel.user_id.in_(
                db.query(SkillListingModel.teacher_id)
                .filter(
                    SkillListingModel.category_id == target_category_id,
                    SkillListingModel.status == "published",
                )
            )
        )

    norm_sort = (sort or "recommended").strip().lower().replace("-", "_")
    if norm_sort == "price_asc":
        query = query.order_by(effective_price.asc(), TeacherProfileModel.experience_years.desc())
    elif norm_sort == "price_desc":
        query = query.order_by(effective_price.desc(), TeacherProfileModel.experience_years.desc())
    elif norm_sort == "experience":
        query = query.order_by(TeacherProfileModel.experience_years.desc(), effective_price.asc())
    elif norm_sort == "rating":
        query = query.order_by(TeacherProfileModel.is_verified.desc(), TeacherProfileModel.experience_years.desc())
    else:  # recommended
        query = query.order_by(TeacherProfileModel.is_verified.desc(), TeacherProfileModel.experience_years.desc())

    total_count = query.count()
    offset = (page - 1) * page_size
    profiles = query.offset(offset).limit(page_size).all()

    cards = [_build_teacher_card(db, p) for p in profiles]

    # If DB is empty, provide curated sample cards for seamless UX
    if total_count == 0:
        filtered_samples = []
        for s in SAMPLE_FEATURED_TEACHERS:
            if q:
                q_lower = q.strip().lower()
                matches_q = (
                    q_lower in s["name"].lower()
                    or q_lower in s["specialty"].lower()
                    or any(q_lower in sk.lower() for sk in s.get("skills", []))
                )
                if not matches_q:
                    continue
            if city and city.lower() not in s["city"].lower():
                continue
            if mode and mode != "all":
                if s["teaching_mode"] != mode and s["teaching_mode"] != "both":
                    continue
            if min_exp is not None and s["experience_years"] < min_exp:
                continue
            if min_price is not None and s["hourly_rate"] < min_price:
                continue
            if max_price is not None and s["hourly_rate"] > max_price:
                continue
            if min_rating is not None and s["rating"] < min_rating:
                continue
            if category:
                cat_lower = category.lower()
                matches_cat = (
                    any(cat_lower in sk.lower() for sk in s.get("skills", []))
                    or cat_lower in s["specialty"].lower()
                )
                if not matches_cat:
                    continue
            filtered_samples.append(s)

        # Apply sorting to fallback samples
        if norm_sort == "price_asc":
            filtered_samples.sort(key=lambda x: x["hourly_rate"])
        elif norm_sort == "price_desc":
            filtered_samples.sort(key=lambda x: x["hourly_rate"], reverse=True)
        elif norm_sort == "experience":
            filtered_samples.sort(key=lambda x: x["experience_years"], reverse=True)
        elif norm_sort == "rating":
            filtered_samples.sort(key=lambda x: x["rating"], reverse=True)
        else:  # recommended
            filtered_samples.sort(key=lambda x: (x["is_verified"], x["rating"]), reverse=True)

        total_count = len(filtered_samples)
        cards = [TeacherCardSchema(**s) for s in filtered_samples[offset : offset + page_size]]

    data = TeacherPaginationSchema(
        total=total_count,
        page=page,
        page_size=page_size,
        teachers=cards,
    ).model_dump(mode="json")

    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Teachers fetched successfully",
        data=data,
    )


def get_teacher_detail(db: Session, user_id: int) -> ApiResponse:
    """Get full public teacher details including active listings."""
    profile = (
        db.query(TeacherProfileModel)
        .filter(TeacherProfileModel.user_id == user_id)
        .first()
    )

    if profile is None:
        # Check sample teachers
        for s in SAMPLE_FEATURED_TEACHERS:
            if s["user_id"] == user_id:
                return ApiResponse(
                    status=status.HTTP_200_OK,
                    message="Teacher details fetched successfully",
                    data=s,
                )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found",
        )

    card = _build_teacher_card(db, profile)
    listings = (
        db.query(SkillListingModel)
        .filter(SkillListingModel.teacher_id == user_id, SkillListingModel.status == "published")
        .all()
    )
    listings_data = [
        {
            "id": l.id,
            "title": l.title,
            "description": l.description,
            "level": l.level,
            "price_amount": float(l.price_amount),
            "currency": l.currency,
            "price_unit": l.price_unit,
            "teaching_mode": l.teaching_mode,
            "city": l.city,
            "area": l.area,
        }
        for l in listings
    ]

    result = card.model_dump(mode="json")
    result["listings"] = listings_data

    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Teacher details fetched successfully",
        data=result,
    )

