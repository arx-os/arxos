"""
Tests for core.shared.date_utils module.

This module contains comprehensive tests for the date and time utility functions
provided by the core.shared.date_utils module.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, Mock

from core.shared.date_utils import (
    get_current_timestamp,
    get_current_timestamp_iso,
    parse_timestamp,
    format_timestamp,
    add_timestamp_to_dict,
    calculate_time_difference,
    is_timestamp_recent,
    get_relative_time_description,
    create_timestamp_range,
    validate_date_range,
    get_quarter_dates,
    get_month_dates,
    format_duration,
    parse_duration,
)


class TestDateUtils:
    """Test date utility functions."""

    def test_get_current_timestamp(self):
        """Test getting current timestamp."""
        timestamp = get_current_timestamp()
        assert isinstance(timestamp, datetime)
        assert timestamp.tzinfo is None  # Should be UTC

    def test_get_current_timestamp_iso(self):
        """Test getting current timestamp as ISO string."""
        timestamp_str = get_current_timestamp_iso()
        assert isinstance(timestamp_str, str)
        assert "T" in timestamp_str
        assert timestamp_str.endswith("Z") or "+" in timestamp_str

    def test_parse_timestamp_datetime(self):
        """Test parsing datetime object."""
        dt = datetime(2024, 1, 1, 12, 0, 0)
        result = parse_timestamp(dt)
        assert result == dt

    def test_parse_timestamp_iso_string(self):
        """Test parsing ISO format string."""
        dt = datetime(2024, 1, 1, 12, 0, 0)
        iso_str = dt.isoformat()
        result = parse_timestamp(iso_str)
        assert result == dt

    def test_parse_timestamp_none(self):
        """Test parsing None timestamp."""
        result = parse_timestamp(None)
        assert result is None

    def test_parse_timestamp_invalid_string(self):
        """Test parsing invalid string."""
        result = parse_timestamp("invalid-date")
        assert result is None

    def test_format_timestamp_iso(self):
        """Test formatting timestamp as ISO."""
        dt = datetime(2024, 1, 1, 12, 0, 0)
        result = format_timestamp(dt, "iso")
        assert result == dt.isoformat()

    def test_format_timestamp_sql(self):
        """Test formatting timestamp as SQL."""
        dt = datetime(2024, 1, 1, 12, 0, 0)
        result = format_timestamp(dt, "sql")
        assert result == "2024-01-01 12:00:00"

    def test_format_timestamp_human(self):
        """Test formatting timestamp as human readable."""
        dt = datetime(2024, 1, 1, 12, 0, 0)
        result = format_timestamp(dt, "human")
        assert "January 1, 2024" in result

    def test_format_timestamp_unknown_format(self):
        """Test formatting with unknown format."""
        dt = datetime(2024, 1, 1, 12, 0, 0)
        result = format_timestamp(dt, "unknown")
        assert result == dt.isoformat()

    def test_add_timestamp_to_dict(self):
        """Test adding timestamp to dictionary."""
        data = {"key": "value"}
        result = add_timestamp_to_dict(data)

        assert "timestamp" in result
        assert result["key"] == "value"
        assert isinstance(result["timestamp"], str)

    def test_add_timestamp_to_dict_custom_key(self):
        """Test adding timestamp with custom key."""
        data = {"key": "value"}
        result = add_timestamp_to_dict(data, "created_at")

        assert "created_at" in result
        assert "timestamp" not in result
        assert result["key"] == "value"

    def test_calculate_time_difference(self):
        """Test calculating time difference."""
        start = datetime(2024, 1, 1, 12, 0, 0)
        end = datetime(2024, 1, 1, 13, 0, 0)

        diff = calculate_time_difference(start, end)
        assert diff == timedelta(hours=1)

    def test_calculate_time_difference_current_time(self):
        """Test calculating time difference with current time."""
        start = datetime(2024, 1, 1, 12, 0, 0)
        diff = calculate_time_difference(start)

        assert isinstance(diff, timedelta)
        assert diff.total_seconds() > 0

    def test_is_timestamp_recent(self):
        """Test checking if timestamp is recent."""
        # Recent timestamp
        recent = datetime.now(timezone.utc) - timedelta(minutes=2)
        assert is_timestamp_recent(recent, max_age_minutes=5) is True

        # Old timestamp
        old = datetime.now(timezone.utc) - timedelta(minutes=10)
        assert is_timestamp_recent(old, max_age_minutes=5) is False

    def test_is_timestamp_recent_none(self):
        """Test checking recent timestamp with None."""
        assert is_timestamp_recent(None) is False

    def test_get_relative_time_description(self):
        """Test getting relative time description."""
        now = datetime.now(timezone.utc)

        # Just now
        just_now = now - timedelta(seconds=30)
        assert "just now" in get_relative_time_description(just_now)

        # Minutes ago
        minutes_ago = now - timedelta(minutes=5)
        assert "5 minutes ago" in get_relative_time_description(minutes_ago)

        # Hours ago
        hours_ago = now - timedelta(hours=2)
        assert "2 hours ago" in get_relative_time_description(hours_ago)

        # Days ago
        days_ago = now - timedelta(days=3)
        assert "3 days ago" in get_relative_time_description(days_ago)

    def test_get_relative_time_description_none(self):
        """Test getting relative time description with None."""
        result = get_relative_time_description(None)
        assert result == "unknown time"

    def test_create_timestamp_range(self):
        """Test creating timestamp range."""
        start, end = create_timestamp_range(days_back=7)

        assert isinstance(start, datetime)
        assert isinstance(end, datetime)
        assert start < end
        assert (end - start).days == 7

    def test_create_timestamp_range_custom_dates(self):
        """Test creating timestamp range with custom dates."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 10)

        start, end = create_timestamp_range(start_date, end_date)
        assert start == start_date
        assert end == end_date

    def test_validate_date_range_valid(self):
        """Test validating valid date range."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 10)

        assert validate_date_range(start, end) is True

    def test_validate_date_range_invalid(self):
        """Test validating invalid date range."""
        start = datetime(2024, 1, 10)
        end = datetime(2024, 1, 1)

        assert validate_date_range(start, end) is False

    def test_get_quarter_dates(self):
        """Test getting quarter dates."""
        start, end = get_quarter_dates(2024, 1)

        assert start == datetime(2024, 1, 1)
        assert end == datetime(2024, 4, 1)

    def test_get_quarter_dates_invalid_quarter(self):
        """Test getting quarter dates with invalid quarter."""
        with pytest.raises(ValueError):
            get_quarter_dates(2024, 5)

    def test_get_month_dates(self):
        """Test getting month dates."""
        start, end = get_month_dates(2024, 3)

        assert start == datetime(2024, 3, 1)
        assert end == datetime(2024, 4, 1)

    def test_get_month_dates_invalid_month(self):
        """Test getting month dates with invalid month."""
        with pytest.raises(ValueError):
            get_month_dates(2024, 13)

    def test_format_duration(self):
        """Test formatting duration."""
        assert "30.0 seconds" in format_duration(30)
        assert "2.5 minutes" in format_duration(150)
        assert "1.5 hours" in format_duration(5400)
        assert "2.0 days" in format_duration(172800)

    def test_parse_duration(self):
        """Test parsing duration strings."""
        assert parse_duration("30s") == timedelta(seconds=30)
        assert parse_duration("5m") == timedelta(minutes=5)
        assert parse_duration("2h") == timedelta(hours=2)
        assert parse_duration("1d") == timedelta(days=1)
        assert parse_duration("30") == timedelta(seconds=30)

    def test_parse_duration_invalid(self):
        """Test parsing invalid duration strings."""
        assert parse_duration("invalid") is None
        assert parse_duration("") is None


if __name__ == "__main__":
    pytest.main([__file__])
