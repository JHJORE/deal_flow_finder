from __future__ import annotations

from datetime import UTC, datetime

import pytest

from pipeline.entities.errors import ValidationError
from pipeline.entities.value_objects import (
    Cik,
    Handle,
    Sector,
    Timestamp,
    Url,
)


class TestHandle:
    def test_strips_leading_at(self) -> None:
        assert Handle("@roelofbotha").value == "roelofbotha"

    def test_accepts_plain(self) -> None:
        assert Handle("roelofbotha").value == "roelofbotha"

    def test_rejects_empty(self) -> None:
        with pytest.raises(ValidationError):
            Handle("")

    def test_rejects_only_at(self) -> None:
        with pytest.raises(ValidationError):
            Handle("@")

    def test_rejects_whitespace(self) -> None:
        with pytest.raises(ValidationError):
            Handle("roe lof")


class TestUrl:
    def test_accepts_https(self) -> None:
        assert Url("https://sequoiacap.com").value == "https://sequoiacap.com"

    def test_accepts_http(self) -> None:
        assert Url("http://example.com").value == "http://example.com"

    def test_rejects_relative(self) -> None:
        with pytest.raises(ValidationError):
            Url("/team")

    def test_rejects_empty(self) -> None:
        with pytest.raises(ValidationError):
            Url("")


class TestTimestamp:
    def test_rejects_naive_datetime(self) -> None:
        with pytest.raises(ValidationError):
            Timestamp(datetime(2024, 1, 1))

    def test_normalises_to_utc(self) -> None:
        from datetime import timedelta
        from datetime import timezone as tz

        plus_two = tz(timedelta(hours=2))
        ts = Timestamp(datetime(2024, 1, 1, 12, 0, tzinfo=plus_two))
        assert ts.value.tzinfo is UTC
        assert ts.value.hour == 10

    def test_from_iso_handles_z(self) -> None:
        ts = Timestamp.from_iso("2024-01-01T00:00:00Z")
        assert ts.value.tzinfo is UTC

    def test_from_iso_rejects_garbage(self) -> None:
        with pytest.raises(ValidationError):
            Timestamp.from_iso("not-a-date")


class TestCik:
    def test_accepts_valid(self) -> None:
        assert Cik(1318605).padded() == "0001318605"

    def test_rejects_zero(self) -> None:
        with pytest.raises(ValidationError):
            Cik(0)

    def test_rejects_negative(self) -> None:
        with pytest.raises(ValidationError):
            Cik(-1)

    def test_rejects_too_long(self) -> None:
        with pytest.raises(ValidationError):
            Cik(10_000_000_000)


class TestSector:
    def test_lowercases_and_collapses_whitespace(self) -> None:
        assert Sector("  AI   Infrastructure ").value == "ai infrastructure"

    def test_rejects_empty(self) -> None:
        with pytest.raises(ValidationError):
            Sector("   ")
