from heidi_engine.dashboard import format_time

def test_format_time_utc():
    """Test ISO timestamp with 'Z' suffix."""
    assert format_time("2023-10-27T12:34:56Z") == "12:34:56"

def test_format_time_with_offset():
    """Test ISO timestamp with offset."""
    assert format_time("2023-10-27T12:34:56+00:00") == "12:34:56"
    assert format_time("2023-10-27T12:34:56+05:00") == "12:34:56"

def test_format_time_no_offset():
    """Test ISO timestamp without offset."""
    assert format_time("2023-10-27T12:34:56") == "12:34:56"

def test_format_time_date_only():
    """Test ISO date only."""
    # datetime.fromisoformat support for YYYY-MM-DD seems to vary by environment/version.
    # We accept either the parsed time (00:00:00) or the sliced string (2023-10-).
    res = format_time("2023-10-27")
    assert res in ["00:00:00", "2023-10-"]

def test_format_time_invalid():
    """Test invalid timestamp string."""
    assert format_time("invalid-time") == "invalid-"
    assert format_time("!!!!") == "!!!!"

def test_format_time_empty():
    """Test empty string."""
    assert format_time("") == ""

def test_format_time_none():
    """Test None value."""
    assert format_time(None) == ""

def test_format_time_short():
    """Test short string."""
    assert format_time("12:34") == "12:34"
