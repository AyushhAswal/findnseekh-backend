import hashlib
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.utils.settings import settings


def create_access_token(user_id: int) -> str:
    """Create a JWT access token for the given user ID."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "_id": user_id,
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_access_token(token: str) -> dict:
    """Decode and verify a JWT token, returning its payload."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


def hash_password(password: str) -> str:
    """Hash a password using Argon2."""
    from pwdlib import PasswordHash
    from pwdlib.hashers.argon2 import Argon2Hasher

    pwd_hash = PasswordHash(hashers=[Argon2Hasher()])
    return pwd_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its Argon2 hash."""
    from pwdlib import PasswordHash
    from pwdlib.hashers.argon2 import Argon2Hasher

    pwd_hash = PasswordHash(hashers=[Argon2Hasher()])
    return pwd_hash.verify(plain_password, hashed_password)


def require_active_session(token: str, db: Session) -> dict:
    """
    Verify the token and check it has not been revoked.
    Returns the decoded payload if valid.
    """
    from src.users.models import RevokedTokenModel

    payload = verify_access_token(token)

    # Check if the token has been revoked
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    revoked = (
        db.query(RevokedTokenModel)
        .filter(RevokedTokenModel.token_hash == token_hash)
        .first()
    )
    if revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )

    return payload


def revoke_token(token: str, db: Session) -> None:
    """Store the SHA-256 hash of the token in the revocation table."""
    from src.users.models import RevokedTokenModel

    import jwt as pyjwt

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    try:
        payload = pyjwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    except pyjwt.InvalidTokenError:
        exp = datetime.now(timezone.utc) + timedelta(hours=1)

    revoked = RevokedTokenModel(token_hash=token_hash, expires_at=exp)
    db.add(revoked)
    db.commit()
