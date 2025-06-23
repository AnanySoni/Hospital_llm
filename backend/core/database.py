import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Use environment variables or default to these test credentials
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:kev1jiph@localhost:5432/hospital_db"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 