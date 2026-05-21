from __future__ import annotations

import pytest

from pipeline.entities.errors import ValidationError
from pipeline.entities.models import (
    Filing,
    Partner,
    Post,
    Signal,
    SocialSnapshot,
    new_id,
)
from pipeline.entities.value_objects import (
    Cik,
    FirmName,
    Handle,
    SignalKind,
    Timestamp,
    Url,
)


def _ts() -> Timestamp:
    return Timestamp.from_iso("2024-01-01T00:00:00Z")


class TestPartner:
    def test_rejects_blank_name(self) -> None:
        with pytest.raises(ValidationError):
            Partner(
                id=new_id(),
                name="   ",
                firm=FirmName.SEQUOIA,
                role="Partner",
                x_handle=Handle("roelofbotha"),
                linkedin_url=None,
                blog_url=None,
                bio="",
            )


class TestPost:
    def test_rejects_negative_counts(self) -> None:
        with pytest.raises(ValidationError):
            Post(
                id=new_id(),
                author_handle=Handle("roelofbotha"),
                text="hi",
                timestamp=_ts(),
                url=Url("https://x.com/roelofbotha/status/1"),
                like_count=-1,
                reply_count=0,
                repost_count=0,
            )


class TestSocialSnapshot:
    def test_rejects_negative_followers(self) -> None:
        with pytest.raises(ValidationError):
            SocialSnapshot(
                handle=Handle("roelofbotha"),
                captured_at=_ts(),
                follower_count=-1,
                following_count=0,
                post_count_30d=0,
                post_count_prior_30d=0,
            )


class TestFiling:
    def test_rejects_blank_issuer(self) -> None:
        with pytest.raises(ValidationError):
            Filing(
                cik=Cik(1),
                issuer_name="",
                raise_amount=1000,
                filing_date=_ts(),
                form_type="D",
                accession_number="0000000000-00-000000",
                source_url=Url("https://efts.sec.gov/x"),
            )

    def test_rejects_negative_raise(self) -> None:
        with pytest.raises(ValidationError):
            Filing(
                cik=Cik(1),
                issuer_name="Acme Inc",
                raise_amount=-5,
                filing_date=_ts(),
                form_type="D",
                accession_number="0000000000-00-000000",
                source_url=Url("https://efts.sec.gov/x"),
            )


class TestSignal:
    def test_rejects_score_out_of_range(self) -> None:
        with pytest.raises(ValidationError):
            Signal(
                id=new_id(),
                kind=SignalKind.PARTNER_ENGAGEMENT_WITH_UNKNOWN,
                score=1.5,
                evidence={},
                detected_at=_ts(),
                narrative=None,
            )
