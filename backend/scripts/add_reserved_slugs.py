"""
Simple migration script to add the reserved_slugs table and seed it with
initial reserved words for hospital slugs.

Run once from the project root (with your .env configured):

    python -m backend.scripts.add_reserved_slugs
"""

import os
from pathlib import Path

from sqlalchemy import Column, String, DateTime, text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(ENV_PATH)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required for add_reserved_slugs migration")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class ReservedSlug(Base):
    __tablename__ = "reserved_slugs"

    slug = Column(String(50), primary_key=True, index=True)
    reason = Column(String(100), nullable=True)
    reserved_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )


INITIAL_RESERVED = [
    ("admin", "system"),
    ("api", "system"),
    ("www", "system"),
    ("support", "system"),
    ("help", "system"),
    ("docs", "system"),
    ("app", "system"),
    ("dashboard", "system"),
    ("login", "system"),
    ("register", "system"),
    ("auth", "system"),
    ("oauth", "system"),
    ("callback", "system"),
    ("health", "system"),
    ("status", "system"),
]


def main():
    # Create table if it doesn't exist
    Base.metadata.create_all(bind=engine, tables=[ReservedSlug.__table__])

    db = SessionLocal()
    try:
        existing = {
            s.slug for s in db.query(ReservedSlug.slug).all()
        }

        created = 0
        now = datetime.utcnow()

        for slug, reason in INITIAL_RESERVED:
            if slug in existing:
                continue
            db.add(
                ReservedSlug(
                    slug=slug.lower(),
                    reason=reason,
                    reserved_at=now,
                )
            )
            created += 1

        if created:
            db.commit()
        print(f"Reserved slugs migration completed. Added {created} new reserved slugs.")
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()


