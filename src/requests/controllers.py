from datetime import datetime, timezone

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.requests.dtos import (
    LearningRequestCreateSchema,
    LearningRequestPublicSchema,
    LearningRequestReadSchema,
)
from src.requests.models import LearningRequestModel
from src.roles.models import RoleModel, UserRoleModel
from src.skills.models import SkillListingModel
from src.users.models import UserModel
from src.utils.auth import require_active_session
from src.utils.responses import ApiResponse


def _check_student_role(db: Session, user_id: int) -> None:
    """Verify the user has the student role."""
    student_role = db.query(RoleModel).filter(RoleModel.name == "student").first()
    if student_role is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student role not available",
        )
    user_role = (
        db.query(UserRoleModel)
        .filter(UserRoleModel.user_id == user_id, UserRoleModel.role_id == student_role.id)
        .first()
    )
    if user_role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a student to perform this action",
        )


def create_learning_request(db: Session, token: str, body: LearningRequestCreateSchema) -> ApiResponse:
    """Send a learning request for a skill listing."""
    payload = require_active_session(token, db)
    student_id = payload.get("_id")
    if student_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    _check_student_role(db, student_id)

    # Get the skill listing
    listing = (
        db.query(SkillListingModel)
        .filter(SkillListingModel.id == body.skill_listing_id)
        .first()
    )
    if listing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill listing not found",
        )

    # Check listing is published
    if listing.status != "published":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only request published listings",
        )

    # Self-request prevention
    teacher_id = listing.teacher_id
    if student_id == teacher_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot request your own listing",
        )

    # Create request with derived IDs
    request = LearningRequestModel(
        skill_listing_id=body.skill_listing_id,
        student_id=student_id,
        teacher_id=teacher_id,
        message=body.message,
        status="pending",
    )
    db.add(request)
    db.commit()
    db.refresh(request)

    return ApiResponse(
        status=status.HTTP_201_CREATED,
        message="Learning request sent successfully",
        data=LearningRequestReadSchema.model_validate(request).model_dump(mode="json"),
    )


def list_sent_requests(db: Session, token: str) -> ApiResponse:
    """List requests sent by the current student."""
    payload = require_active_session(token, db)
    student_id = payload.get("_id")
    if student_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    requests = (
        db.query(LearningRequestModel)
        .filter(LearningRequestModel.student_id == student_id)
        .order_by(LearningRequestModel.created_at.desc())
        .all()
    )

    data = []
    for req in requests:
        listing = db.query(SkillListingModel).filter(SkillListingModel.id == req.skill_listing_id).first()
        teacher = db.query(UserModel).filter(UserModel.id == req.teacher_id).first()
        data.append(LearningRequestPublicSchema(
            id=req.id,
            skill_listing_id=req.skill_listing_id,
            skill_title=listing.title if listing else "Unknown",
            student_id=req.student_id,
            student_name="You",
            teacher_id=req.teacher_id,
            teacher_name=teacher.name if teacher else "Unknown",
            message=req.message,
            status=req.status,
            teacher_response=req.teacher_response,
            responded_at=req.responded_at,
            created_at=req.created_at,
        ).model_dump(mode="json"))

    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Sent requests fetched successfully",
        data=data,
    )


def list_received_requests(db: Session, token: str) -> ApiResponse:
    """List requests received by the current teacher."""
    payload = require_active_session(token, db)
    teacher_id = payload.get("_id")
    if teacher_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    requests = (
        db.query(LearningRequestModel)
        .filter(LearningRequestModel.teacher_id == teacher_id)
        .order_by(LearningRequestModel.created_at.desc())
        .all()
    )

    data = []
    for req in requests:
        listing = db.query(SkillListingModel).filter(SkillListingModel.id == req.skill_listing_id).first()
        student = db.query(UserModel).filter(UserModel.id == req.student_id).first()
        data.append(LearningRequestPublicSchema(
            id=req.id,
            skill_listing_id=req.skill_listing_id,
            skill_title=listing.title if listing else "Unknown",
            student_id=req.student_id,
            student_name=student.name if student else "Unknown",
            teacher_id=req.teacher_id,
            teacher_name="You",
            message=req.message,
            status=req.status,
            teacher_response=req.teacher_response,
            responded_at=req.responded_at,
            created_at=req.created_at,
        ).model_dump(mode="json"))

    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Received requests fetched successfully",
        data=data,
    )


def get_learning_request(db: Session, token: str, request_id: int) -> ApiResponse:
    """View a learning request if the current user is a participant."""
    payload = require_active_session(token, db)
    user_id = payload.get("_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    request = db.query(LearningRequestModel).filter(LearningRequestModel.id == request_id).first()
    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning request not found",
        )

    # Only student or teacher can view
    if request.student_id != user_id and request.teacher_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this request",
        )

    listing = db.query(SkillListingModel).filter(SkillListingModel.id == request.skill_listing_id).first()
    student = db.query(UserModel).filter(UserModel.id == request.student_id).first()
    teacher = db.query(UserModel).filter(UserModel.id == request.teacher_id).first()

    data = LearningRequestPublicSchema(
        id=request.id,
        skill_listing_id=request.skill_listing_id,
        skill_title=listing.title if listing else "Unknown",
        student_id=request.student_id,
        student_name=student.name if student else "Unknown",
        teacher_id=request.teacher_id,
        teacher_name=teacher.name if teacher else "Unknown",
        message=request.message,
        status=request.status,
        teacher_response=request.teacher_response,
        responded_at=request.responded_at,
        created_at=request.created_at,
    ).model_dump(mode="json")

    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Learning request fetched successfully",
        data=data,
    )


def accept_request(db: Session, token: str, request_id: int) -> ApiResponse:
    """Accept a pending learning request (teacher only)."""
    payload = require_active_session(token, db)
    teacher_id = payload.get("_id")
    if teacher_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    request = db.query(LearningRequestModel).filter(LearningRequestModel.id == request_id).first()
    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning request not found",
        )

    if request.teacher_id != teacher_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the intended teacher can accept this request",
        )

    if request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending requests can be accepted",
        )

    request.status = "accepted"
    request.responded_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(request)

    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Learning request accepted successfully",
        data=LearningRequestReadSchema.model_validate(request).model_dump(mode="json"),
    )


def reject_request(db: Session, token: str, request_id: int) -> ApiResponse:
    """Reject a pending learning request (teacher only)."""
    payload = require_active_session(token, db)
    teacher_id = payload.get("_id")
    if teacher_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    request = db.query(LearningRequestModel).filter(LearningRequestModel.id == request_id).first()
    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning request not found",
        )

    if request.teacher_id != teacher_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the intended teacher can reject this request",
        )

    if request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending requests can be rejected",
        )

    request.status = "rejected"
    request.responded_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(request)

    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Learning request rejected successfully",
        data=LearningRequestReadSchema.model_validate(request).model_dump(mode="json"),
    )


def cancel_request(db: Session, token: str, request_id: int) -> ApiResponse:
    """Cancel a pending learning request (student only)."""
    payload = require_active_session(token, db)
    student_id = payload.get("_id")
    if student_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    request = db.query(LearningRequestModel).filter(LearningRequestModel.id == request_id).first()
    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning request not found",
        )

    if request.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the requesting student can cancel this request",
        )

    if request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending requests can be cancelled",
        )

    request.status = "cancelled"
    db.commit()
    db.refresh(request)

    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Learning request cancelled successfully",
        data=LearningRequestReadSchema.model_validate(request).model_dump(mode="json"),
    )
