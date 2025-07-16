"""
Date and Time Utilities for Arxos Platform

Provides standardized date/time manipulation functions used across
the platform. Centralizes common datetime operations to ensure
consistency and reduce code duplication.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Dict, Any
import structlog

logger = structlog.get_logger(__name__)

def get_current_timestamp() -> datetime:
    """
    Get current UTC timestamp.
    
    Returns:
        Current UTC datetime (naive)
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)

def get_current_timestamp_iso() -> str:
    """
    Get current UTC timestamp as ISO format string.
    
    Returns:
        Current UTC datetime as ISO format string with timezone
    """
    return datetime.now(timezone.utc).isoformat()

def parse_timestamp(timestamp: Union[str, datetime, None]) -> Optional[datetime]:
    """
    Parse timestamp from various formats.
    
    Args:
        timestamp: Timestamp as string, datetime, or None
        
    Returns:
        Parsed datetime or None if invalid
    """
    if timestamp is None:
        return None
    
    if isinstance(timestamp, datetime):
        return timestamp
    
    if isinstance(timestamp, str):
        try:
            # Try ISO format first
            return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            try:
                # Try common formats
                for fmt in [
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%dT%H:%M:%S',
                    '%Y-%m-%dT%H:%M:%S.%f',
                    '%Y-%m-%dT%H:%M:%S.%fZ',
                    '%Y-%m-%dT%H:%M:%SZ'
                ]:
                    try:
                        return datetime.strptime(timestamp, fmt)
                    except ValueError:
                        continue
            except Exception as e:
                logger.warning("timestamp_parse_failed",
                             timestamp=timestamp,
                             error=str(e))
                return None
    
    logger.warning("invalid_timestamp_type",
                  timestamp=timestamp,
                  timestamp_type=type(timestamp).__name__)
    return None

def format_timestamp(dt: datetime, format_type: str = "iso") -> str:
    """
    Format datetime to string.
    
    Args:
        dt: Datetime to format
        format_type: Format type ("iso", "sql", "human")
        
    Returns:
        Formatted datetime string
    """
    if dt is None:
        return ""
    
    if format_type == "iso":
        return dt.isoformat()
    elif format_type == "sql":
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    elif format_type == "human":
        day = str(dt.day)
        return dt.strftime(f'%B {day}, %Y at %I:%M %p')
    else:
        logger.warning("unknown_timestamp_format",
                      format_type=format_type)
        return dt.isoformat()

def add_timestamp_to_dict(data: Dict[str, Any], key: str = "timestamp") -> Dict[str, Any]:
    """
    Add current timestamp to dictionary.
    
    Args:
        data: Dictionary to add timestamp to
        key: Key name for timestamp
        
    Returns:
        Dictionary with added timestamp
    """
    data_copy = data.copy()
    data_copy[key] = get_current_timestamp_iso()
    return data_copy

def calculate_time_difference(start_time: datetime, end_time: Optional[datetime] = None) -> timedelta:
    """
    Calculate time difference between two timestamps.
    
    Args:
        start_time: Start timestamp
        end_time: End timestamp (uses current time if None)
        
    Returns:
        Time difference as timedelta
    """
    if end_time is None:
        end_time = get_current_timestamp()
    
    # Convert timezone-aware datetimes to naive for compatibility
    if start_time.tzinfo is not None:
        start_time = start_time.replace(tzinfo=None)
    if end_time.tzinfo is not None:
        end_time = end_time.replace(tzinfo=None)
    
    return end_time - start_time

def is_timestamp_recent(timestamp: datetime, max_age_minutes: int = 5) -> bool:
    """
    Check if timestamp is recent (within specified minutes).
    
    Args:
        timestamp: Timestamp to check
        max_age_minutes: Maximum age in minutes
        
    Returns:
        True if timestamp is recent
    """
    if timestamp is None:
        return False
    
    age = calculate_time_difference(timestamp)
    return age.total_seconds() < (max_age_minutes * 60)

def get_relative_time_description(timestamp: datetime) -> str:
    """
    Get human-readable relative time description.
    
    Args:
        timestamp: Timestamp to describe
        
    Returns:
        Human-readable relative time string
    """
    if timestamp is None:
        return "unknown time"
    
    now = get_current_timestamp()
    
    # Convert timezone-aware datetimes to naive for compatibility
    if timestamp.tzinfo is not None:
        timestamp = timestamp.replace(tzinfo=None)
    if now.tzinfo is not None:
        now = now.replace(tzinfo=None)
    
    diff = now - timestamp
    
    if diff.total_seconds() < 60:
        return "just now"
    elif diff.total_seconds() < 3600:
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.days < 7:
        days = diff.days
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif diff.days < 30:
        weeks = diff.days // 7
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    elif diff.days < 365:
        months = diff.days // 30
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = diff.days // 365
        return f"{years} year{'s' if years != 1 else ''} ago"

def create_timestamp_range(start_date: Optional[datetime] = None, 
                         end_date: Optional[datetime] = None,
                         days_back: Optional[int] = None) -> tuple[datetime, datetime]:
    """
    Create a timestamp range for queries.
    
    Args:
        start_date: Start date (optional)
        end_date: End date (optional)
        days_back: Days to go back from current time (optional)
        
    Returns:
        Tuple of (start_datetime, end_datetime)
    """
    now = get_current_timestamp()
    
    if end_date is None:
        end_date = now
    
    if start_date is None:
        if days_back is not None:
            start_date = now - timedelta(days=days_back)
        else:
            start_date = now - timedelta(days=7)  # Default to 7 days
    
    return start_date, end_date

def validate_date_range(start_date: datetime, end_date: datetime) -> bool:
    """
    Validate that start date is before end date.
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        True if valid date range
    """
    return start_date < end_date

def get_quarter_dates(year: int, quarter: int) -> tuple[datetime, datetime]:
    """
    Get start and end dates for a quarter.
    
    Args:
        year: Year
        quarter: Quarter (1-4)
        
    Returns:
        Tuple of (start_date, end_date) for the quarter
    """
    if quarter < 1 or quarter > 4:
        raise ValueError("Quarter must be between 1 and 4")
    
    quarter_starts = [
        datetime(year, 1, 1),
        datetime(year, 4, 1),
        datetime(year, 7, 1),
        datetime(year, 10, 1)
    ]
    
    start_date = quarter_starts[quarter - 1]
    
    if quarter == 4:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = quarter_starts[quarter]
    
    return start_date, end_date

def get_month_dates(year: int, month: int) -> tuple[datetime, datetime]:
    """
    Get start and end dates for a month.
    
    Args:
        year: Year
        month: Month (1-12)
        
    Returns:
        Tuple of (start_date, end_date) for the month
    """
    if month < 1 or month > 12:
        raise ValueError("Month must be between 1 and 12")
    
    start_date = datetime(year, month, 1)
    
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    return start_date, end_date

def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Human-readable duration string
    """
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f} hours"
    else:
        days = seconds / 86400
        return f"{days:.1f} days"

def parse_duration(duration_str: str) -> Optional[timedelta]:
    """
    Parse duration string to timedelta.
    
    Args:
        duration_str: Duration string (e.g., "1h", "30m", "2d")
        
    Returns:
        Timedelta or None if invalid
    """
    try:
        # Remove spaces and convert to lowercase
        duration_str = duration_str.strip().lower()
        
        # Parse common patterns
        if duration_str.endswith('s'):
            seconds = float(duration_str[:-1])
            return timedelta(seconds=seconds)
        elif duration_str.endswith('m'):
            minutes = float(duration_str[:-1])
            return timedelta(minutes=minutes)
        elif duration_str.endswith('h'):
            hours = float(duration_str[:-1])
            return timedelta(hours=hours)
        elif duration_str.endswith('d'):
            days = float(duration_str[:-1])
            return timedelta(days=days)
        else:
            # Try to parse as seconds
            seconds = float(duration_str)
            return timedelta(seconds=seconds)
    except (ValueError, TypeError):
        logger.warning("duration_parse_failed",
                      duration_str=duration_str)
        return None 