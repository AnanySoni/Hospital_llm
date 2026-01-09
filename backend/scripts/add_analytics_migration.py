"""
Migration script to add analytics and UX enhancement features:
- OnboardingAnalytics table
- OnboardingSession.step_started_at and step_timings columns
- Indexes for performance
"""
import os
import sys
from pathlib import Path

# Add parent directory to path to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text, inspect
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

engine = create_engine(DATABASE_URL)


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def index_exists(table_name: str, index_name: str) -> bool:
    """Check if an index exists on a table."""
    inspector = inspect(engine)
    indexes = [idx['name'] for idx in inspector.get_indexes(table_name)]
    return index_name in indexes


def run_migration():
    """Run the analytics migration."""
    logger.info("Starting analytics migration...")
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # 1. Create OnboardingAnalytics table
            if not table_exists('onboarding_analytics'):
                logger.info("Creating onboarding_analytics table...")
                conn.execute(text("""
                    CREATE TABLE onboarding_analytics (
                        id SERIAL PRIMARY KEY,
                        onboarding_session_id INTEGER,
                        admin_user_id INTEGER,
                        event_type VARCHAR(50) NOT NULL,
                        event_data TEXT,
                        step_number INTEGER,
                        time_spent_seconds INTEGER,
                        signup_method VARCHAR(20),
                        ip_address VARCHAR(45),
                        user_agent TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (onboarding_session_id) REFERENCES onboarding_sessions(id),
                        FOREIGN KEY (admin_user_id) REFERENCES admin_users(id)
                    )
                """))
                logger.info("✅ Created onboarding_analytics table")
            else:
                logger.info("⏭️  onboarding_analytics table already exists")
            
            # 2. Create indexes on onboarding_analytics
            if not index_exists('onboarding_analytics', 'ix_onboarding_analytics_event_type'):
                logger.info("Creating index on onboarding_analytics.event_type...")
                conn.execute(text("""
                    CREATE INDEX ix_onboarding_analytics_event_type 
                    ON onboarding_analytics(event_type)
                """))
                logger.info("✅ Created index on event_type")
            
            if not index_exists('onboarding_analytics', 'ix_onboarding_analytics_created_at'):
                logger.info("Creating index on onboarding_analytics.created_at...")
                conn.execute(text("""
                    CREATE INDEX ix_onboarding_analytics_created_at 
                    ON onboarding_analytics(created_at)
                """))
                logger.info("✅ Created index on created_at")
            
            # 3. Add step_started_at and step_timings to onboarding_sessions
            if not table_exists('onboarding_sessions'):
                logger.warning("⚠️  onboarding_sessions table does not exist. Skipping column additions.")
            else:
                if not column_exists('onboarding_sessions', 'step_started_at'):
                    logger.info("Adding 'step_started_at' column to onboarding_sessions...")
                    conn.execute(text("""
                        ALTER TABLE onboarding_sessions 
                        ADD COLUMN step_started_at TIMESTAMP NULL
                    """))
                    logger.info("✅ Added 'step_started_at' column")
                else:
                    logger.info("⏭️  'step_started_at' column already exists")
                
                if not column_exists('onboarding_sessions', 'step_timings'):
                    logger.info("Adding 'step_timings' column to onboarding_sessions...")
                    conn.execute(text("""
                        ALTER TABLE onboarding_sessions 
                        ADD COLUMN step_timings TEXT DEFAULT '{}'
                    """))
                    logger.info("✅ Added 'step_timings' column")
                else:
                    logger.info("⏭️  'step_timings' column already exists")
            
            trans.commit()
            logger.info("✅ Analytics migration completed successfully!")
            
        except Exception as e:
            trans.rollback()
            logger.error(f"❌ Migration failed: {str(e)}")
            raise


if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        logger.error(f"Migration error: {str(e)}")
        sys.exit(1)

