from __future__ import annotations

from pathlib import Path

from pipeline.adapters.storage.json_repository import JsonFileRepository


def test_round_trip(tmp_path: Path) -> None:
    repo = JsonFileRepository(tmp_path)
    repo.save("firm_graph", {"partners": [{"name": "Roelof"}]})
    assert repo.load("firm_graph") == {"partners": [{"name": "Roelof"}]}


def test_nested_keys_create_dirs(tmp_path: Path) -> None:
    repo = JsonFileRepository(tmp_path)
    repo.save("social/roelof", {"posts": []})
    assert (tmp_path / "social" / "roelof.json").exists()


def test_atomic_write_leaves_no_tmp(tmp_path: Path) -> None:
    repo = JsonFileRepository(tmp_path)
    repo.save("a", {"x": 1})
    assert list(tmp_path.glob("*.tmp")) == []


def test_load_missing_returns_none(tmp_path: Path) -> None:
    repo = JsonFileRepository(tmp_path)
    assert repo.load("nope") is None


def test_list_keys_prefix(tmp_path: Path) -> None:
    repo = JsonFileRepository(tmp_path)
    repo.save("social/a", 1)
    repo.save("social/b", 2)
    repo.save("linkedin/c", 3)
    assert repo.list_keys("social") == ["social/a", "social/b"]
