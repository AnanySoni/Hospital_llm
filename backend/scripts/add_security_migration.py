"""
Migration script to add security and validation features:
- RateLimitLog table
- EmailVerification.used and used_at columns
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
from sqlalchemy.exc import ProgrammingError
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
    """Run the security migration."""
    logger.info("Starting security migration...")
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # 1. Create RateLimitLog table
            if not table_exists('rate_limit_logs'):
                logger.info("Creating rate_limit_logs table...")
                conn.execute(text("""
                    CREATE TABLE rate_limit_logs (
                        id SERIAL PRIMARY KEY,
                        identifier VARCHAR(255) NOT NULL,
                        endpoint VARCHAR(100) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                logger.info("✅ Created rate_limit_logs table")
            else:
                logger.info("⏭️  rate_limit_logs table already exists")
            
            # 2. Create indexes on rate_limit_logs
            if not index_exists('rate_limit_logs', 'ix_rate_limit_logs_identifier'):
                logger.info("Creating index on rate_limit_logs.identifier...")
                conn.execute(text("""
                    CREATE INDEX ix_rate_limit_logs_identifier 
                    ON rate_limit_logs(identifier)
                """))
                logger.info("✅ Created index on identifier")
            
            if not index_exists('rate_limit_logs', 'ix_rate_limit_logs_endpoint'):
                logger.info("Creating index on rate_limit_logs.endpoint...")
                conn.execute(text("""
                    CREATE INDEX ix_rate_limit_logs_endpoint 
                    ON rate_limit_logs(endpoint)
                """))
                logger.info("✅ Created index on endpoint")
            
            if not index_exists('rate_limit_logs', 'ix_rate_limit_logs_created_at'):
                logger.info("Creating index on rate_limit_logs.created_at...")
                conn.execute(text("""
                    CREATE INDEX ix_rate_limit_logs_created_at 
                    ON rate_limit_logs(created_at)
                """))
                logger.info("✅ Created index on created_at")
            
            if not index_exists('rate_limit_logs', 'idx_identifier_endpoint_created'):
                logger.info("Creating composite index on rate_limit_logs...")
                conn.execute(text("""
                    CREATE INDEX idx_identifier_endpoint_created 
                    ON rate_limit_logs(identifier, endpoint, created_at)
                """))
                logger.info("✅ Created composite index")
            
            # 3. Add used and used_at columns to email_verifications
            if not table_exists('email_verifications'):
                logger.warning("⚠️  email_verifications table does not exist. Skipping column additions.")
            else:
                if not column_exists('email_verifications', 'used'):
                    logger.info("Adding 'used' column to email_verifications...")
                    conn.execute(text("""
                        ALTER TABLE email_verifications 
                        ADD COLUMN used BOOLEAN NOT NULL DEFAULT FALSE
                    """))
                    logger.info("✅ Added 'used' column")
                else:
                    logger.info("⏭️  'used' column already exists")
                
                if not column_exists('email_verifications', 'used_at'):
                    logger.info("Adding 'used_at' column to email_verifications...")
                    conn.execute(text("""
                        ALTER TABLE email_verifications 
                        ADD COLUMN used_at TIMESTAMP NULL
                    """))
                    logger.info("✅ Added 'used_at' column")
                else:
                    logger.info("⏭️  'used_at' column already exists")
                
                # Create index on used column for performance
                if not index_exists('email_verifications', 'ix_email_verifications_used'):
                    logger.info("Creating index on email_verifications.used...")
                    conn.execute(text("""
                        CREATE INDEX ix_email_verifications_used 
                        ON email_verifications(used)
                    """))
                    logger.info("✅ Created index on used column")
            
            trans.commit()
            logger.info("✅ Security migration completed successfully!")
            
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

