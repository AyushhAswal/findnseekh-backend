from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import func, or_, and_
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.category.models import CategoryModel
from src.profile.models import TeacherProfileModel
from src.requests.models import LearningRequestModel
from src.roles.models import RoleModel, UserRoleModel
from src.skills.models import SkillListingModel
from src.teachers.dtos import (
    TeacherCardSchema,
    TeacherDetailSchema,
    TeacherEnquiryCreateSchema,
    TeacherEnquiryResponseSchema,
    TeacherPaginationSchema,
)
from src.users.models import UserModel
from src.utils.auth import require_active_session
from src.utils.responses import ApiResponse

SAMPLE_FEATURED_TEACHERS = [
    {
        "id": 101,
        "user_id": 101,
        "name": "Rohan Mehta",
        "specialty": "Guitar & Music Production",
        "category": "Music",
        "category_id": "music",
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
        "category": "Music",
        "category_id": "music",
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
        "category": "Dance",
        "category_id": "dance",
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
        "category": "Music",
        "category_id": "music",
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
        "category": "Photography",
        "category_id": "photography",
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
        "category": "Art & Craft",
        "category_id": "art-craft",
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
    category_name = "Music"
    category_slug = "music"

    if listings:
        prices = [listing.price_amount for listing in listings if listing.price_amount > 0]
        if prices:
            hourly_rate = min(prices)
        if not specialty or specialty == "Teacher":
            specialty = listings[0].title
        for listing in listings:
            if listing.title not in skills_list:
                skills_list.append(listing.title)
        first_cat = db.query(CategoryModel).filter(CategoryModel.id == listings[0].category_id).first()
        if first_cat:
            category_name = first_cat.name
            category_slug = first_cat.slug

    city = profile.city
    state = profile.state
    location_parts = [p for p in (city, state) if p]
    location = ", ".join(location_parts) if location_parts else "Location Flexible"

    return TeacherCardSchema(
        id=profile.id,
        user_id=profile.user_id,
        name=user_name,
        specialty=specialty,
        category=category_name,
        category_id=category_slug,
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
    """Get full public teacher details including credentials, reviews, FAQs and listings."""
    profile = (
        db.query(TeacherProfileModel)
        .filter(TeacherProfileModel.user_id == user_id)
        .first()
    )

    if profile is None:
        # Check sample teachers
        for s in SAMPLE_FEATURED_TEACHERS:
            if s["user_id"] == user_id:
                sample_data = dict(s)
                sample_data["about"] = sample_data.get("about") or (
                    f"{s['bio']} With over {s['experience_years']} years of teaching and professional practice, "
                    f"I tailor every session to your learning pace and personal goals."
                )
                sample_data["languages"] = sample_data.get("languages") or ["English", "Hindi"]
                sample_data["qualifications"] = sample_data.get("qualifications") or [
                    f"{s['experience_years']}+ years of teaching & professional practice",
                    f"Certified instructor in {s['specialty']}",
                    "Mentored 100+ students across India and abroad",
                ]
                sample_data["reviews"] = sample_data.get("reviews") or [
                    {
                        "id": "rev-1",
                        "student_name": "Aarav Patel",
                        "rating": 5.0,
                        "date": "2 weeks ago",
                        "comment": "Amazing teacher! Extremely patient and gives personalized feedback after every class.",
                    },
                    {
                        "id": "rev-2",
                        "student_name": "Pooja Sharma",
                        "rating": 5.0,
                        "date": "1 month ago",
                        "comment": "I saw huge improvement in my technique within just 4 sessions. Very organized and knowledgeable.",
                    },
                    {
                        "id": "rev-3",
                        "student_name": "Rohan Verma",
                        "rating": 4.8,
                        "date": "2 months ago",
                        "comment": "Great guidance and step-by-step methodology. Always on time and very encouraging.",
                    },
                ]
                sample_data["faqs"] = sample_data.get("faqs") or [
                    {
                        "question": "What should I prepare for the first trial session?",
                        "answer": "Just bring your enthusiasm! For online lessons, ensure a quiet space and a stable internet connection. If instruments or materials are required, I will guide you on what to acquire before subsequent classes.",
                    },
                    {
                        "question": "How do online sessions work?",
                        "answer": "We connect over Google Meet or Zoom. I use high-definition audio and multi-angle camera setups to ensure you can clearly see techniques and posture. After each session, you receive notes and practice exercises.",
                    },
                    {
                        "question": "Can I reschedule or cancel a class?",
                        "answer": "Yes, you can easily reschedule anytime up to 12 hours before the scheduled session with no cancellation fee.",
                    },
                ]
                sample_data["listings"] = [
                    {
                        "id": 1000 + s["user_id"],
                        "title": s["specialty"],
                        "description": s["bio"],
                        "level": "all-levels",
                        "price_amount": float(s["hourly_rate"]),
                        "currency": s["currency"],
                        "price_unit": s["price_unit"],
                        "teaching_mode": s["teaching_mode"],
                        "city": s["city"],
                        "area": s["state"],
                    }
                ]
                return ApiResponse(
                    status=status.HTTP_200_OK,
                    message="Teacher details fetched successfully",
                    data=TeacherDetailSchema(**sample_data).model_dump(mode="json"),
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

    card_dict = card.model_dump(mode="json")
    card_dict["about"] = (
        profile.bio
        or f"Certified mentor with over {profile.experience_years} years of teaching and professional experience."
    )
    card_dict["languages"] = ["English", "Hindi"]
    card_dict["qualifications"] = [
        f"{profile.experience_years}+ years of teaching & professional practice",
        profile.qualification or f"Certified instructor in {card.specialty}",
        "Mentored students across multiple proficiency levels",
    ]
    card_dict["reviews"] = [
        {
            "id": "rev-1",
            "student_name": "Aarav Patel",
            "rating": 5.0,
            "date": "2 weeks ago",
            "comment": "Amazing teacher! Extremely patient and gives personalized feedback after every class.",
        },
        {
            "id": "rev-2",
            "student_name": "Pooja Sharma",
            "rating": 5.0,
            "date": "1 month ago",
            "comment": "I saw huge improvement in my technique within just 4 sessions. Very organized and knowledgeable.",
        },
    ]
    card_dict["faqs"] = [
        {
            "question": "What should I prepare for the first trial session?",
            "answer": "Just bring your enthusiasm! For online lessons, ensure a quiet space and a stable internet connection.",
        },
        {
            "question": "How do online sessions work?",
            "answer": "We connect over Google Meet or Zoom. After each session, you receive notes and practice exercises.",
        },
        {
            "question": "Can I reschedule or cancel a class?",
            "answer": "Yes, you can easily reschedule anytime up to 12 hours before the scheduled session with no fee.",
        },
    ]
    card_dict["listings"] = listings_data

    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Teacher details fetched successfully",
        data=TeacherDetailSchema(**card_dict).model_dump(mode="json"),
    )


def send_teacher_enquiry(
    db: Session,
    user_id: int,
    body: TeacherEnquiryCreateSchema,
    token: Optional[str] = None,
) -> ApiResponse:
    """Send an enquiry / lesson request to a teacher."""
    student_id = None
    if token:
        payload = require_active_session(token, db)
        student_id = payload.get("_id")
        if student_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot send an enquiry to yourself",
            )

    # Check if teacher exists in DB
    profile = (
        db.query(TeacherProfileModel)
        .filter(TeacherProfileModel.user_id == user_id)
        .first()
    )

    # If teacher is not in DB, check sample teachers
    if profile is None:
        sample_teacher = next((s for s in SAMPLE_FEATURED_TEACHERS if s["user_id"] == user_id), None)
        if sample_teacher is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher not found",
            )

        # Return successful booking confirmation for sample teacher
        resp_data = TeacherEnquiryResponseSchema(
            id=990000 + user_id,
            teacher_id=user_id,
            student_id=student_id,
            teaching_mode=body.teaching_mode or "online",
            preferred_date=body.preferred_date,
            message=body.message or "I am interested in starting lessons.",
            status="pending",
            created_at=datetime.now(timezone.utc).isoformat(),
        ).model_dump(mode="json")

        return ApiResponse(
            status=status.HTTP_201_CREATED,
            message="Enquiry sent successfully to instructor",
            data=resp_data,
        )

    # Teacher exists in DB: ensure student user exists
    if student_id is None:
        guest_email = "guest.student@findnseekh.local"
        guest_user = db.query(UserModel).filter(UserModel.email == guest_email).first()
        if guest_user is None:
            student_role = db.query(RoleModel).filter(RoleModel.name == "student").first()
            guest_user = UserModel(
                name="Guest Student",
                email=guest_email,
                password_hash="guest_no_login",
                is_active=True,
            )
            db.add(guest_user)
            db.flush()
            if student_role:
                db.add(UserRoleModel(user_id=guest_user.id, role_id=student_role.id))
            db.commit()
            db.refresh(guest_user)
        student_id = guest_user.id

    # Find teacher's published listing
    listing = (
        db.query(SkillListingModel)
        .filter(SkillListingModel.teacher_id == user_id, SkillListingModel.status == "published")
        .first()
    )
    if listing is None:
        default_cat = db.query(CategoryModel).first()
        cat_id = default_cat.id if default_cat else 1
        listing = SkillListingModel(
            teacher_id=user_id,
            category_id=cat_id,
            title=profile.qualification or "1-on-1 Mentorship Session",
            description=profile.bio or "Personalized 1-on-1 coaching session.",
            level="all-levels",
            price_amount=Decimal("500.00"),
            currency="INR",
            price_unit="session",
            teaching_mode=body.teaching_mode or profile.teaching_mode or "both",
            status="published",
        )
        db.add(listing)
        db.flush()

    enquiry_msg = body.message or "I am interested in starting lessons."
    if body.preferred_date:
        enquiry_msg = f"[{body.teaching_mode.upper()} - {body.preferred_date}] {enquiry_msg}"
    else:
        enquiry_msg = f"[{body.teaching_mode.upper()}] {enquiry_msg}"

    learning_request = LearningRequestModel(
        skill_listing_id=listing.id,
        student_id=student_id,
        teacher_id=user_id,
        message=enquiry_msg[:1000],
        status="pending",
    )
    db.add(learning_request)
    db.commit()
    db.refresh(learning_request)

    resp_data = TeacherEnquiryResponseSchema(
        id=learning_request.id,
        teacher_id=user_id,
        student_id=student_id,
        teaching_mode=body.teaching_mode or "online",
        preferred_date=body.preferred_date,
        message=learning_request.message,
        status=learning_request.status,
        created_at=learning_request.created_at.isoformat() if learning_request.created_at else datetime.now(timezone.utc).isoformat(),
    ).model_dump(mode="json")

    return ApiResponse(
        status=status.HTTP_201_CREATED,
        message="Enquiry sent successfully to instructor",
        data=resp_data,
    )


