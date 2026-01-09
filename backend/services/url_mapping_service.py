"""
URL Mapping Service for Hospital Multi-Tenant SaaS
Handles slug generation, validation (including reserved slugs),
conflict resolution, and mapping slugs to hospital_id.
"""

import re
from typing import Optional, List, Dict, Any

from sqlalchemy import text

from backend.core.database import SessionLocal
from backend.core.models import Hospital


class URLMappingService:
    """
    Central place for slug generation and validation.

    Responsibilities:
    - Format validation (lowercase, a-z0-9-, length)
    - Reserved slug checks (reserved_slugs table)
    - Uniqueness checks against hospitals.slug
    - Suggesting alternative slugs when taken/reserved
    """

    SLUG_REGEX = re.compile(r"^[a-z0-9-]+$")
    MIN_LENGTH = 3
    MAX_LENGTH = 50

    @staticmethod
    def generate_slug(name: str) -> str:
        """Generate a URL-friendly base slug from a hospital name."""
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", name.lower()).strip("-")
        slug = re.sub(r"-+", "-", slug)
        return slug

    # ------------------------------------------------------------------
    # Core checks
    # ------------------------------------------------------------------
    @classmethod
    def is_slug_unique(cls, slug: str) -> bool:
        """Check if the slug is unique in the hospitals table."""
        db = SessionLocal()
        try:
            return not db.query(Hospital).filter_by(slug=slug).first()
        finally:
            db.close()

    @classmethod
    def is_slug_reserved(cls, slug: str) -> bool:
        """Check if the slug appears in the reserved_slugs table."""
        # Use a lightweight text query so we don't need a SQLAlchemy model here
        db = SessionLocal()
        try:
            result = db.execute(
                text("SELECT slug FROM reserved_slugs WHERE slug = :slug LIMIT 1"),
                {"slug": slug.lower()},
            ).first()
            return result is not None
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Validation & suggestion API
    # ------------------------------------------------------------------
    @classmethod
    def validate_slug(cls, slug: str) -> Dict[str, Any]:
        """
        Validate slug format, reserved status, and uniqueness.

        Returns a dict:
        {
            "valid": bool,        # passes format & length rules
            "available": bool,    # not reserved and not used
            "reason": Optional[str]  # machine-readable reason if not available/invalid
        }
        """
        raw = slug or ""
        slug = raw.strip().lower()

        # Format / length validation
        if not slug:
            return {"valid": False, "available": False, "reason": "empty"}

        if len(slug) < cls.MIN_LENGTH:
            return {"valid": False, "available": False, "reason": "too_short"}

        if len(slug) > cls.MAX_LENGTH:
            return {"valid": False, "available": False, "reason": "too_long"}

        if not cls.SLUG_REGEX.match(slug):
            return {"valid": False, "available": False, "reason": "invalid_format"}

        # Reserved check
        if cls.is_slug_reserved(slug):
            return {"valid": True, "available": False, "reason": "reserved"}

        # Uniqueness check
        if not cls.is_slug_unique(slug):
            return {"valid": True, "available": False, "reason": "taken"}

        return {"valid": True, "available": True, "reason": None}

    @classmethod
    def get_unique_slug(cls, base_slug: str) -> str:
        """
        Generate a unique, non-reserved slug, appending a number if needed.
        """
        # Normalize base
        base = base_slug.strip().lower()
        if not base:
            base = "hospital"

        # Ensure base respects format/length as much as possible
        base = cls.generate_slug(base) or "hospital"

        slug = base
        counter = 2
        while True:
            result = cls.validate_slug(slug)
            if result["valid"] and result["available"]:
                return slug
            slug = f"{base}-{counter}"
            counter += 1

    @classmethod
    def suggest_alternatives(cls, base_slug: str, max_suggestions: int = 3) -> List[str]:
        """
        Suggest alternative slugs based on a base slug.

        - Starts from a cleaned version of base_slug.
        - Includes the base if it's valid & available.
        - Then appends -2, -3, ... until it finds enough suggestions.
        """
        suggestions: List[str] = []

        base = base_slug.strip().lower()
        if not base:
            base = "hospital"

        base = cls.generate_slug(base) or "hospital"

        # First try the base itself
        result = cls.validate_slug(base)
        if result["valid"] and result["available"]:
            suggestions.append(base)

        counter = 2
        while len(suggestions) < max_suggestions and counter < 50:
            candidate = f"{base}-{counter}"
            res = cls.validate_slug(candidate)
            if res["valid"] and res["available"]:
                suggestions.append(candidate)
            counter += 1

        return suggestions

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------
    @staticmethod
    def map_slug_to_hospital_id(slug: str) -> Optional[int]:
        """Map a slug to its hospital_id."""
        db = SessionLocal()
        try:
            hospital = db.query(Hospital).filter_by(slug=slug).first()
            return hospital.id if hospital else None
        finally:
            db.close()

    @staticmethod
    def create_slug_for_hospital(name: str) -> str:
        """
        Create and assign a unique slug for a new hospital.
        Respects reserved slugs and uniqueness constraints.
        """
        base_slug = URLMappingService.generate_slug(name)
        unique_slug = URLMappingService.get_unique_slug(base_slug)
        return unique_slug

