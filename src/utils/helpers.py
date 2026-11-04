import re
from typing import Optional


def generate_slug(text: str) -> str:
    """Generate a URL-friendly slug from a string."""
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    slug = re.sub(r"^-+|-+$", "", slug)
    return slug


def mask_phone(phone: Optional[str]) -> Optional[str]:
    """Mask a phone number, showing only the last 4 digits."""
    if not phone:
        return None
    if len(phone) < 4:
        return "****"
    return "*" * (len(phone) - 4) + phone[-4:]
