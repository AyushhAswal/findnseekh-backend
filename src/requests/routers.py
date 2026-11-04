from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.requests import controllers
from src.requests.dtos import LearningRequestCreateSchema
from src.utils.db import get_db

security = HTTPBearer()
request_routes = APIRouter(prefix="/requests", tags=["Learning Request"])


@request_routes.post("", status_code=status.HTTP_201_CREATED)
def create_request(
    body: LearningRequestCreateSchema,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Send a learning request for a skill listing."""
    token = credentials.credentials
    return controllers.create_learning_request(db, token, body)


@request_routes.get("/sent", status_code=status.HTTP_200_OK)
def list_sent(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """List own sent requests."""
    token = credentials.credentials
    return controllers.list_sent_requests(db, token)


@request_routes.get("/received", status_code=status.HTTP_200_OK)
def list_received(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """List requests received by current teacher."""
    token = credentials.credentials
    return controllers.list_received_requests(db, token)


@request_routes.get("/{request_id}", status_code=status.HTTP_200_OK)
def get_request(
    request_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """View a request if current user is a participant."""
    token = credentials.credentials
    return controllers.get_learning_request(db, token, request_id)


@request_routes.patch("/{request_id}/accept", status_code=status.HTTP_200_OK)
def accept(
    request_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Accept a pending request (teacher only)."""
    token = credentials.credentials
    return controllers.accept_request(db, token, request_id)


@request_routes.patch("/{request_id}/reject", status_code=status.HTTP_200_OK)
def reject(
    request_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Reject a pending request (teacher only)."""
    token = credentials.credentials
    return controllers.reject_request(db, token, request_id)


@request_routes.patch("/{request_id}/cancel", status_code=status.HTTP_200_OK)
def cancel(
    request_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Cancel own pending request (student only)."""
    token = credentials.credentials
    return controllers.cancel_request(db, token, request_id)
