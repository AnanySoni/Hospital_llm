"""
Service for tracking onboarding metrics and analytics.
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.core.models import OnboardingAnalytics, OnboardingSession
import json
import logging

logger = logging.getLogger(__name__)


class OnboardingAnalyticsService:
    """Service for tracking onboarding metrics."""

    @staticmethod
    def track_event(
        db: Session,
        event_type: str,
        onboarding_session_id: int = None,
        admin_user_id: int = None,
        step_number: int = None,
        event_data: dict = None,
        signup_method: str = None,
        ip_address: str = None,
        user_agent: str = None,
    ):
        """Track an onboarding event."""
        # Calculate time spent on step
        time_spent = None
        if onboarding_session_id and step_number:
            session = db.query(OnboardingSession).filter_by(
                id=onboarding_session_id
            ).first()
            if session and session.step_started_at:
                time_spent = int(
                    (datetime.utcnow() - session.step_started_at).total_seconds()
                )

        analytics = OnboardingAnalytics(
            onboarding_session_id=onboarding_session_id,
            admin_user_id=admin_user_id,
            event_type=event_type,
            event_data=json.dumps(event_data or {}),
            step_number=step_number,
            time_spent_seconds=time_spent,
            signup_method=signup_method,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(analytics)
        db.commit()
        logger.info(f"Tracked event: {event_type} for session {onboarding_session_id}")

    @staticmethod
    def track_step_start(
        db: Session,
        onboarding_session_id: int,
        step_number: int,
    ):
        """Mark when a step starts."""
        session = db.query(OnboardingSession).filter_by(
            id=onboarding_session_id
        ).first()
        if session:
            session.step_started_at = datetime.utcnow()
            db.commit()
            logger.info(f"Step {step_number} started for session {onboarding_session_id}")

    @staticmethod
    def get_analytics_summary(db: Session, days: int = 30) -> dict:
        """Get analytics summary for dashboard."""
        cutoff = datetime.utcnow() - timedelta(days=days)

        # Registration start rate
        registration_starts = db.query(OnboardingAnalytics).filter(
            OnboardingAnalytics.event_type == 'registration_start',
            OnboardingAnalytics.created_at > cutoff
        ).count()

        # Completion rate
        completions = db.query(OnboardingAnalytics).filter(
            OnboardingAnalytics.event_type == 'onboarding_completed',
            OnboardingAnalytics.created_at > cutoff
        ).count()

        # Drop-off points
        drop_offs = db.query(OnboardingAnalytics).filter(
            OnboardingAnalytics.event_type == 'drop_off',
            OnboardingAnalytics.created_at > cutoff
        ).all()

        # Signup method ratio
        google_signups = db.query(OnboardingAnalytics).filter(
            OnboardingAnalytics.event_type == 'registration_start',
            OnboardingAnalytics.signup_method == 'google',
            OnboardingAnalytics.created_at > cutoff
        ).count()

        email_signups = db.query(OnboardingAnalytics).filter(
            OnboardingAnalytics.event_type == 'registration_start',
            OnboardingAnalytics.signup_method == 'email',
            OnboardingAnalytics.created_at > cutoff
        ).count()

        # Calculate average time per step
        step_completions = db.query(OnboardingAnalytics).filter(
            OnboardingAnalytics.event_type == 'step_complete',
            OnboardingAnalytics.created_at > cutoff,
            OnboardingAnalytics.time_spent_seconds.isnot(None)
        ).all()

        avg_time_per_step = {}
        if step_completions:
            step_times = {}
            for event in step_completions:
                step = event.step_number
                if step:
                    if step not in step_times:
                        step_times[step] = []
                    if event.time_spent_seconds:
                        step_times[step].append(event.time_spent_seconds)

            for step, times in step_times.items():
                if times:
                    avg_time_per_step[step] = sum(times) / len(times)

        return {
            'registration_starts': registration_starts,
            'completions': completions,
            'completion_rate': completions / registration_starts if registration_starts > 0 else 0,
            'drop_offs': len(drop_offs),
            'drop_off_points': [d.step_number for d in drop_offs if d.step_number],
            'signup_methods': {
                'google': google_signups,
                'email': email_signups,
                'total': google_signups + email_signups,
            },
            'average_time_per_step': avg_time_per_step,
        }

    @staticmethod
    def get_detailed_analytics(db: Session, days: int = 30) -> dict:
        """Get detailed per-step analytics."""
        cutoff = datetime.utcnow() - timedelta(days=days)

        # Get all step completion events
        step_events = db.query(OnboardingAnalytics).filter(
            OnboardingAnalytics.event_type.in_(['step_complete', 'step_start']),
            OnboardingAnalytics.created_at > cutoff
        ).order_by(OnboardingAnalytics.step_number, OnboardingAnalytics.created_at).all()

        # Group by step
        step_stats = {}
        for event in step_events:
            step = event.step_number
            if not step:
                continue

            if step not in step_stats:
                step_stats[step] = {
                    'starts': 0,
                    'completions': 0,
                    'total_time': 0,
                    'time_count': 0,
                }

            if event.event_type == 'step_start':
                step_stats[step]['starts'] += 1
            elif event.event_type == 'step_complete':
                step_stats[step]['completions'] += 1
                if event.time_spent_seconds:
                    step_stats[step]['total_time'] += event.time_spent_seconds
                    step_stats[step]['time_count'] += 1

        # Calculate averages
        for step, stats in step_stats.items():
            if stats['time_count'] > 0:
                stats['average_time'] = stats['total_time'] / stats['time_count']
            else:
                stats['average_time'] = 0
            stats['completion_rate'] = (
                stats['completions'] / stats['starts'] if stats['starts'] > 0 else 0
            )

        return step_stats

    @staticmethod
    def anonymize_old_ips(db: Session, days: int = 30):
        """Anonymize IP addresses older than specified days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        updated = db.query(OnboardingAnalytics).filter(
            OnboardingAnalytics.ip_address.isnot(None),
            OnboardingAnalytics.created_at < cutoff
        ).update({OnboardingAnalytics.ip_address: None})
        
        db.commit()
        logger.info(f"Anonymized {updated} IP addresses older than {days} days")
        return updated

