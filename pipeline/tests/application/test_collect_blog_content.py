from __future__ import annotations

from pipeline.application.use_cases.collect_blog_content import CollectBlogContent
from pipeline.entities.models import BlogPost, new_id
from pipeline.entities.value_objects import Timestamp, Url
from pipeline.tests.application.fakes import FakeRepository, FakeWebFetcher


def test_fills_body_and_persists() -> None:
    post = BlogPost(
        id=new_id(),
        author_partner_id="p1",
        title="Founder Mode",
        body="",
        published_at=Timestamp.now(),
        source_url=Url("https://example.com/post"),
    )
    web = FakeWebFetcher(pages={"https://example.com/post": "## Founder Mode\n\nbody"})
    repo = FakeRepository()
    out = CollectBlogContent(web=web, repo=repo).execute([post])
    assert out[0].body.startswith("## Founder Mode")
    assert repo.store[f"content/{post.id}"]["body"].startswith("## Founder Mode")


def test_skips_failed_fetches() -> None:
    post = BlogPost(
        id=new_id(),
        author_partner_id="p1",
        title="x",
        body="",
        published_at=Timestamp.now(),
        source_url=Url("https://example.com/missing"),
    )
    web = FakeWebFetcher(fail_urls={"https://example.com/missing"})
    out = CollectBlogContent(web=web, repo=FakeRepository()).execute([post])
    assert out == []
