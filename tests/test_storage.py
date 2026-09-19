import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import pytest
from storage import EventStore, ValidationError, CATEGORIES


@pytest.fixture
def store_path(tmp_path):
    return str(tmp_path / "events.json")


def test_starts_empty(store_path):
    s = EventStore(store_path)
    assert s.events == []


def test_add_and_persist(store_path):
    s = EventStore(store_path)
    ev = s.add("2026-09-25", "work", "Ship the report")
    assert ev.category == "work"
    assert os.path.exists(store_path)

    reloaded = EventStore(store_path)
    assert len(reloaded.events) == 1
    assert reloaded.events[0].description == "Ship the report"


@pytest.mark.parametrize("bad_date", ["2026-13-01", "not-a-date", "", "2026/09/25"])
def test_add_rejects_bad_date(store_path, bad_date):
    s = EventStore(store_path)
    with pytest.raises(ValidationError):
        s.add(bad_date, "work", "something")


def test_add_rejects_bad_category(store_path):
    s = EventStore(store_path)
    with pytest.raises(ValidationError):
        s.add("2026-09-25", "not-a-category", "something")


def test_add_rejects_empty_description(store_path):
    s = EventStore(store_path)
    with pytest.raises(ValidationError):
        s.add("2026-09-25", "work", "   ")


def test_delete_by_full_id(store_path):
    s = EventStore(store_path)
    ev = s.add("2026-09-25", "work", "Ship it")
    assert s.delete(ev.id) is True
    assert s.events == []


def test_delete_by_prefix(store_path):
    s = EventStore(store_path)
    ev = s.add("2026-09-25", "work", "Ship it")
    assert s.delete(ev.id[:8]) is True


def test_delete_unknown_returns_false(store_path):
    s = EventStore(store_path)
    assert s.delete("does-not-exist") is False


def test_malformed_rows_are_skipped_on_load(store_path):
    with open(store_path, "w") as f:
        json.dump([
            {"id": "a", "date": "2026-09-25", "category": "work", "description": "good"},
            {"id": "b", "date": "not-a-date", "category": "work", "description": "bad date"},
            {"id": "c", "date": "2026-09-26", "category": "not-real", "description": "bad category"},
            {"id": "d", "date": "2026-09-27", "category": "work", "description": ""},
            {"id": "e", "date": "2026-09-28"},  # missing fields entirely
        ], f)
    s = EventStore(store_path)
    assert len(s.events) == 1
    assert s.events[0].description == "good"


def test_corrupt_json_file_starts_empty_not_crashing(store_path):
    with open(store_path, "w") as f:
        f.write("{not valid json")
    s = EventStore(store_path)  # must not raise
    assert s.events == []


def test_search_matches_description_date_and_category(store_path):
    s = EventStore(store_path)
    s.add("2026-09-25", "work", "Ship the Q3 report")
    s.add("2026-10-01", "personal", "Dentist appointment")

    assert len(s.search("report")) == 1
    assert len(s.search("2026-10")) == 1
    assert len(s.search("personal")) == 1
    assert len(s.search("nonexistent")) == 0


def test_by_month(store_path):
    s = EventStore(store_path)
    s.add("2026-09-01", "work", "a")
    s.add("2026-09-30", "study", "b")
    s.add("2026-10-01", "urgent", "c")
    assert len(s.by_month(2026, 9)) == 2
    assert len(s.by_month(2026, 10)) == 1


def test_counts_by_category(store_path):
    s = EventStore(store_path)
    s.add("2026-09-01", "work", "a")
    s.add("2026-09-02", "work", "b")
    s.add("2026-09-03", "urgent", "c")
    counts = s.counts_by_category()
    assert counts["work"] == 2
    assert counts["urgent"] == 1
    assert counts["personal"] == 0
    assert set(counts) == set(CATEGORIES)


def test_next_n_days(store_path):
    import datetime
    s = EventStore(store_path)
    today = datetime.date(2026, 9, 18)
    s.add((today + datetime.timedelta(days=2)).isoformat(), "work", "soon")
    s.add((today + datetime.timedelta(days=10)).isoformat(), "work", "later")
    s.add((today - datetime.timedelta(days=1)).isoformat(), "work", "past")
    upcoming = s.next_n_days(7, today=today)
    assert len(upcoming) == 1
    assert upcoming[0].description == "soon"


def test_to_csv(store_path, tmp_path):
    s = EventStore(store_path)
    s.add("2026-09-25", "work", "Ship the report")
    csv_path = str(tmp_path / "out.csv")
    s.to_csv(csv_path)
    content = open(csv_path).read()
    assert "date,category,description" in content or "id,date,category,description" in content
    assert "Ship the report" in content
