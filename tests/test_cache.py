"""Tests for data/cache.py — must pass immediately in Phase 0."""

import time

from data.cache import cache_get, cache_put, cache_get_stale, cache_invalidate


NAMESPACE = "test"


def test_put_and_get(tmp_path, monkeypatch):
    import data.cache as cm
    monkeypatch.setattr(cm, "CACHE_DIR", tmp_path)

    cache_put(NAMESPACE, "key1", b"hello")
    result = cache_get(NAMESPACE, "key1", ttl_seconds=3600)
    assert result == b"hello"


def test_get_expired(tmp_path, monkeypatch):
    import data.cache as cm
    monkeypatch.setattr(cm, "CACHE_DIR", tmp_path)

    cache_put(NAMESPACE, "key2", b"data")
    meta_path = tmp_path / NAMESPACE / "key2.meta"
    import json
    meta = json.loads(meta_path.read_text())
    meta["written_at"] = time.time() - 10000
    meta_path.write_text(json.dumps(meta))

    result = cache_get(NAMESPACE, "key2", ttl_seconds=100)
    assert result is None


def test_get_stale(tmp_path, monkeypatch):
    import data.cache as cm
    monkeypatch.setattr(cm, "CACHE_DIR", tmp_path)

    cache_put(NAMESPACE, "key3", b"stale_data")
    meta_path = tmp_path / NAMESPACE / "key3.meta"
    import json
    meta = json.loads(meta_path.read_text())
    meta["written_at"] = 0
    meta_path.write_text(json.dumps(meta))

    assert cache_get(NAMESPACE, "key3", ttl_seconds=100) is None
    assert cache_get_stale(NAMESPACE, "key3") == b"stale_data"


def test_invalidate(tmp_path, monkeypatch):
    import data.cache as cm
    monkeypatch.setattr(cm, "CACHE_DIR", tmp_path)

    cache_put(NAMESPACE, "key4", b"remove_me")
    assert cache_invalidate(NAMESPACE, "key4") is True
    assert cache_get(NAMESPACE, "key4", ttl_seconds=3600) is None
    assert cache_invalidate(NAMESPACE, "key4") is False


def test_get_missing(tmp_path, monkeypatch):
    import data.cache as cm
    monkeypatch.setattr(cm, "CACHE_DIR", tmp_path)

    assert cache_get(NAMESPACE, "nonexistent", ttl_seconds=3600) is None
    assert cache_get_stale(NAMESPACE, "nonexistent") is None
