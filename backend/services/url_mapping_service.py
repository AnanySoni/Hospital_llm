"""
URL Mapping Service for Multi-Tenant Hospital SaaS
Handles slug generation, uniqueness validation, conflict resolution, and mapping slugs to hospital_id.
"""

import re
from typing import Optional
from backend.core.database import db_session
from backend.core.models import Hospital

class URLMappingService:
    SLUG_REGEX = re.compile(r'^[a-z0-9-]+$')

    @staticmethod
    def generate_slug(name: str) -> str:
        """Generate a URL-friendly slug from hospital name."""
        slug = re.sub(r'[^a-zA-Z0-9]+', '-', name.lower()).strip('-')
        slug = re.sub(r'-+', '-', slug)
        return slug

    @classmethod
    def is_slug_unique(cls, slug: str) -> bool:
        """Check if the slug is unique in the database."""
        return not db_session.query(Hospital).filter_by(slug=slug).first()

    @classmethod
    def get_unique_slug(cls, base_slug: str) -> str:
        """Generate a unique slug, appending a number if needed."""
        slug = base_slug
        counter = 2
        while not cls.is_slug_unique(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    @classmethod
    def validate_slug(cls, slug: str) -> bool:
        """Validate slug format and uniqueness."""
        if not cls.SLUG_REGEX.match(slug):
            return False
        return cls.is_slug_unique(slug)

    @staticmethod
    def map_slug_to_hospital_id(slug: str) -> Optional[int]:
        """Map a slug to its hospital_id."""
        hospital = db_session.query(Hospital).filter_by(slug=slug).first()
        return hospital.id if hospital else None

    @staticmethod
    def create_slug_for_hospital(name: str) -> str:
        """Create and assign a unique slug for a new hospital."""
        base_slug = URLMappingService.generate_slug(name)
        unique_slug = URLMappingService.get_unique_slug(base_slug)
        return unique_slug
"""
URL Mapping Service for Hospital Multi-Tenant SaaS
Handles slug generation, uniqueness validation, conflict resolution, and mapping slugs to hospital_id.
"""

import re
from typing import Optional
from backend.core.database import db_session
from backend.core.models import Hospital

class URLMappingService:
    SLUG_REGEX = re.compile(r'^[a-z0-9-]+$')

    @staticmethod
    def generate_slug(name: str) -> str:
        """Generate a URL-friendly slug from hospital name."""
        slug = re.sub(r'[^a-zA-Z0-9]+', '-', name.lower()).strip('-')
        slug = re.sub(r'-+', '-', slug)
        return slug

    @classmethod
    def is_slug_unique(cls, slug: str) -> bool:
        """Check if the slug is unique in the database."""
        return not db_session.query(Hospital).filter_by(slug=slug).first()

    @classmethod
    def get_unique_slug(cls, base_slug: str) -> str:
        """Generate a unique slug, appending a number if needed."""
        slug = base_slug
        counter = 2
        while not cls.is_slug_unique(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    @classmethod
    def validate_slug(cls, slug: str) -> bool:
        """Validate slug format and uniqueness."""
        if not cls.SLUG_REGEX.match(slug):
            return False
        return cls.is_slug_unique(slug)

    @staticmethod
    def map_slug_to_hospital_id(slug: str) -> Optional[int]:
        """Map a slug to its hospital_id."""
        hospital = db_session.query(Hospital).filter_by(slug=slug).first()
        return hospital.id if hospital else None

    @staticmethod
    def create_slug_for_hospital(name: str) -> str:
        """Create and assign a unique slug for a new hospital."""
        base_slug = URLMappingService.generate_slug(name)
        unique_slug = URLMappingService.get_unique_slug(base_slug)
        return unique_slug
