from datetime import datetime, timedelta, timezone


def parse_nba_date(date_str: str) -> datetime:
    """Parse a date string from NBA API into a UTC datetime object"""
    try:
        # Handle different date formats from NBA API
        formats = [
            "%Y-%m-%d",  # 2024-01-15
            "%Y-%m-%dT%H:%M:%S",  # 2024-01-15T19:30:00
            "%m/%d/%Y",  # 01/15/2024
            "%m/%d/%Y %H:%M:%S",  # 01/15/2024 19:30:00
            "%B %d, %Y",  # January 15, 2024
            "%b %d, %Y",  # Jan 15, 2024
        ]

        parsed_dt = None
        for fmt in formats:
            try:
                parsed_dt = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue

        if parsed_dt is None:
            raise ValueError(f"Could not parse date string: {date_str}")

        # NBA API dates are in US/Eastern time (ET)
        # Convert to UTC by adding 4 or 5 hours depending on daylight saving
        # This is a simplification - we'll use 4 hours (EDT) as default
        et_offset = timezone(timedelta(hours=-4))
        dt_et = parsed_dt.replace(tzinfo=et_offset)
        return dt_et.astimezone(timezone.utc)
    except Exception as e:
        raise ValueError(f"Error parsing date {date_str}: {str(e)}")
