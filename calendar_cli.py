#!/usr/bin/env python3
"""
calendar_cli.py — terminal event calendar.

Built first, before the Streamlit UI, to get the data model, JSON
persistence and input validation right without a UI to hide behind —
the same order I'd want between a scheduled job and the dashboard on
top of it. Same storage.EventStore backing both this and app.py, so
events added here show up there and vice versa.

Examples:
    python calendar_cli.py add 2026-09-25 work "Ship the Q3 report"
    python calendar_cli.py list --month 2026-09
    python calendar_cli.py search report
    python calendar_cli.py stats
    python calendar_cli.py export events.csv
    python calendar_cli.py delete a1b2c3d4
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from storage import EventStore, CATEGORIES, ValidationError


def _fmt(e):
    return f"{e.id[:8]}  {e.date}  {e.category:<9} {e.description}"


def cmd_add(store, args):
    try:
        ev = store.add(args.date, args.category, args.description)
    except ValidationError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print("added " + _fmt(ev))
    return 0


def cmd_delete(store, args):
    if store.delete(args.id):
        print(f"deleted {args.id}")
        return 0
    print(f"no unique event matches id/prefix '{args.id}'", file=sys.stderr)
    return 1


def cmd_list(store, args):
    if args.month:
        try:
            year, month = (int(x) for x in args.month.split("-"))
        except ValueError:
            print("error: --month must be YYYY-MM", file=sys.stderr)
            return 1
        events = store.by_month(year, month)
    else:
        events = sorted(store.events, key=lambda e: e.date)
    if not events:
        print("no events")
        return 0
    for e in events:
        print(_fmt(e))
    return 0


def cmd_search(store, args):
    events = store.search(args.query)
    if not events:
        print("no matches")
        return 0
    for e in events:
        print(_fmt(e))
    return 0


def cmd_stats(store, args):
    by_cat = store.counts_by_category()
    print("by category:")
    for c, n in by_cat.items():
        print(f"  {c:<9} {n}")
    print(f"total: {len(store.events)}")
    upcoming = store.next_n_days(7)
    print(f"\nnext 7 days: {len(upcoming)} event(s)")
    for e in upcoming:
        print("  " + _fmt(e))
    return 0


def cmd_export(store, args):
    store.to_csv(args.path)
    print(f"wrote {args.path}")
    return 0


def build_parser():
    p = argparse.ArgumentParser(description="Terminal event calendar (JSON-backed).")
    p.add_argument("--store", default="events.json", help="path to the JSON event store (default: events.json)")
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("add", help="add an event")
    a.add_argument("date", help="YYYY-MM-DD")
    a.add_argument("category", choices=CATEGORIES)
    a.add_argument("description")
    a.set_defaults(func=cmd_add)

    d = sub.add_parser("delete", help="delete an event by id or unambiguous id prefix")
    d.add_argument("id")
    d.set_defaults(func=cmd_delete)

    l = sub.add_parser("list", help="list events, optionally for one month")
    l.add_argument("--month", help="YYYY-MM")
    l.set_defaults(func=cmd_list)

    s = sub.add_parser("search", help="search description, date, or category")
    s.add_argument("query")
    s.set_defaults(func=cmd_search)

    st = sub.add_parser("stats", help="counts by category, plus what's due in the next 7 days")
    st.set_defaults(func=cmd_stats)

    e = sub.add_parser("export", help="export all events to CSV")
    e.add_argument("path")
    e.set_defaults(func=cmd_export)

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    store = EventStore(args.store)
    return args.func(store, args)


if __name__ == "__main__":
    sys.exit(main())
