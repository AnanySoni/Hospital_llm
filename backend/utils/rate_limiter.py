"""
Rate limiting utilities for preventing abuse and ensuring security.
Uses database-based rate limiting (no Redis dependency).
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from backend.core.models import RateLimitLog


class DatabaseRateLimiter:
    """Database-based rate limiter for endpoints."""
    
    def check_rate_limit(
        self,
        db: Session,
        identifier: str,  # IP address or user_id
        endpoint: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, Optional[int]]:
        """
        Check rate limit using database.
        
        Args:
            db: Database session
            identifier: IP address or user_id
            endpoint: Endpoint path
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
        
        Returns:
            Tuple[bool, Optional[int]]: (allowed, remaining_requests)
        """
        cutoff_time = datetime.utcnow() - timedelta(seconds=window_seconds)
        
        # Count recent requests
        count = db.query(RateLimitLog).filter(
            RateLimitLog.identifier == identifier,
            RateLimitLog.endpoint == endpoint,
            RateLimitLog.created_at > cutoff_time
        ).count()
        
        if count >= max_requests:
            # Still log the attempt for audit
            log_entry = RateLimitLog(
                identifier=identifier,
                endpoint=endpoint
            )
            db.add(log_entry)
            db.commit()
            return False, 0
        
        # Log this request
        log_entry = RateLimitLog(
            identifier=identifier,
            endpoint=endpoint
        )
        db.add(log_entry)
        db.commit()
        
        remaining = max_requests - count - 1
        return True, remaining
    
    def cleanup_old_logs(self, db: Session, days_to_keep: int = 7):
        """
        Clean up old rate limit logs to prevent database bloat.
        
        Args:
            db: Database session
            days_to_keep: Number of days of logs to keep
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days_to_keep)
        
        deleted_count = db.query(RateLimitLog).filter(
            RateLimitLog.created_at < cutoff_time
        ).delete()
        
        db.commit()
        return deleted_count


# Global instance
rate_limiter = DatabaseRateLimiter()

