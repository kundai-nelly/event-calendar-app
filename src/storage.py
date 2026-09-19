"""
storage.py — JSON-backed event store.

The core data model shared by calendar.py (terminal) and app.py (Streamlit):
one JSON array on disk, one Event per entry, four fixed categories. Events
are written to disk on every change and reloaded on start. A malformed
entry (bad date, unknown category, missing description) is skipped on load
rather than allowed to take down the whole read path — one bad row shouldn't
make the calendar unusable.
"""
import csv
import json
import os
import uuid
from dataclasses import dataclass, asdict
from datetime import date as date_cls
from typing import List, Optional

CATEGORIES = ["work", "personal", "study", "urgent"]


@dataclass
class Event:
    id: str
    date: str  # ISO format, YYYY-MM-DD
    category: str
    description: str


class ValidationError(ValueError):
    pass


def _validate_date(value: str) -> str:
    try:
        date_cls.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValidationError(f"'{value}' is not a valid date (expected YYYY-MM-DD)")
    return value


def _validate_category(value: str) -> str:
    if value not in CATEGORIES:
        raise ValidationError(f"category must be one of {CATEGORIES}, got '{value}'")
    return value


def _validate_description(value: str) -> str:
    value = (value or "").strip()
    if not value:
        raise ValidationError("description must not be empty")
    return value


class EventStore:
    """A flat-file JSON store of events, loaded on construction and
    persisted after every mutation."""

    def __init__(self, path: str = "events.json"):
        self.path = path
        self.events: List[Event] = []
        self.load()

    # ---------- persistence ----------

    def load(self):
        self.events = []
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except (json.JSONDecodeError, OSError):
            return  # corrupt store: start empty rather than crash
        for item in raw if isinstance(raw, list) else []:
            try:
                d = _validate_date(item["date"])
                cat = _validate_category(item["category"])
                desc = _validate_description(item.get("description", ""))
            except (ValidationError, KeyError, TypeError):
                continue  # skip malformed rows silently, same as the notebook version
            self.events.append(Event(
                id=item.get("id") or str(uuid.uuid4()),
                date=d, category=cat, description=desc,
            ))

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump([asdict(e) for e in self.events], f, indent=2)

    # ---------- mutation ----------

    def add(self, date: str, category: str, description: str) -> Event:
        date = _validate_date(date)
        category = _validate_category(category)
        description = _validate_description(description)
        ev = Event(id=str(uuid.uuid4()), date=date, category=category, description=description)
        self.events.append(ev)
        self.save()
        return ev

    def delete(self, id_or_prefix: str) -> bool:
        """Delete by full id or an unambiguous prefix (as printed by the CLI)."""
        matches = [e for e in self.events if e.id == id_or_prefix or e.id.startswith(id_or_prefix)]
        if len(matches) != 1:
            return False
        self.events = [e for e in self.events if e.id != matches[0].id]
        self.save()
        return True

    # ---------- queries ----------

    def search(self, query: str) -> List[Event]:
        q = query.lower().strip()
        if not q:
            return sorted(self.events, key=lambda e: e.date)
        return sorted(
            (e for e in self.events if q in e.description.lower() or q in e.date or q in e.category),
            key=lambda e: e.date,
        )

    def by_month(self, year: int, month: int) -> List[Event]:
        prefix = f"{year:04d}-{month:02d}"
        return sorted((e for e in self.events if e.date.startswith(prefix)), key=lambda e: e.date)

    def counts_by_category(self) -> dict:
        out = {c: 0 for c in CATEGORIES}
        for e in self.events:
            out[e.category] += 1
        return out

    def counts_by_month(self) -> dict:
        out = {}
        for e in sorted(self.events, key=lambda e: e.date):
            key = e.date[:7]
            out[key] = out.get(key, 0) + 1
        return out

    def next_n_days(self, n: int = 7, today: Optional[date_cls] = None) -> List[Event]:
        today = today or date_cls.today()
        upcoming = []
        for e in self.events:
            diff = (date_cls.fromisoformat(e.date) - today).days
            if 0 <= diff <= n:
                upcoming.append(e)
        return sorted(upcoming, key=lambda e: e.date)

    def to_csv(self, path: str):
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "date", "category", "description"])
            for e in sorted(self.events, key=lambda e: e.date):
                writer.writerow([e.id, e.date, e.category, e.description])
