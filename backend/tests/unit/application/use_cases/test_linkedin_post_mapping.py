from datetime import datetime

from deal_flow.application.use_cases.linkedin_post_mapping import to_snapshot


def test_maps_realistic_post_with_reactions_comments_and_repost():
    raw = [
        {
            "id": "urn:li:activity:1",
            "postUrl": "https://linkedin.com/posts/1",
            "text": "hello",
            "postedAt": "2026-04-01T10:00:00Z",
            "author": {"name": "Alice", "linkedinUrl": "https://linkedin.com/in/alice"},
            "reactionsCount": 12,
            "commentsCount": 3,
            "reactions": [
                {
                    "reactionType": "LIKE",
                    "actor": {"name": "Bob", "linkedinUrl": "https://linkedin.com/in/bob"},
                }
            ],
            "comments": [{"text": "great", "author": {"name": "Carol"}}],
        },
        {"id": "2", "repostedPost": {"id": "1", "text": "original"}},
    ]
    snap = to_snapshot("https://linkedin.com/in/alice", raw)

    assert len(snap.posts) == 2
    p = snap.posts[0]
    assert p.text == "hello"
    assert p.posted_at == datetime.fromisoformat("2026-04-01T10:00:00+00:00")
    assert p.author_name == "Alice"
    assert p.reactions_count == 12
    assert p.reactions[0].reaction_type == "LIKE"
    assert p.reactions[0].actor_name == "Bob"
    assert p.comments[0].text == "great"
    assert [r.id for r in snap.reposts] == ["2"]
