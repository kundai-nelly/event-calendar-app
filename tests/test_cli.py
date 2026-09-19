import os
import subprocess
import sys

CLI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "calendar_cli.py")


def run(args, store_path):
    return subprocess.run(
        [sys.executable, CLI, "--store", store_path, *args],
        capture_output=True, text=True,
    )


def test_add_and_list(tmp_path):
    store_path = str(tmp_path / "events.json")
    r = run(["add", "2026-09-25", "work", "Ship the report"], store_path)
    assert r.returncode == 0
    assert "added" in r.stdout

    r = run(["list"], store_path)
    assert r.returncode == 0
    assert "Ship the report" in r.stdout


def test_add_rejects_bad_date(tmp_path):
    store_path = str(tmp_path / "events.json")
    r = run(["add", "not-a-date", "work", "x"], store_path)
    assert r.returncode == 1
    assert "error" in r.stderr


def test_search(tmp_path):
    store_path = str(tmp_path / "events.json")
    run(["add", "2026-09-25", "work", "Ship the report"], store_path)
    run(["add", "2026-10-01", "personal", "Dentist"], store_path)
    r = run(["search", "dentist"], store_path)
    assert "Dentist" in r.stdout
    assert "Ship" not in r.stdout


def test_stats(tmp_path):
    store_path = str(tmp_path / "events.json")
    run(["add", "2026-09-25", "work", "a"], store_path)
    run(["add", "2026-09-26", "urgent", "b"], store_path)
    r = run(["stats"], store_path)
    assert "total: 2" in r.stdout


def test_export(tmp_path):
    store_path = str(tmp_path / "events.json")
    csv_path = str(tmp_path / "out.csv")
    run(["add", "2026-09-25", "work", "Ship the report"], store_path)
    r = run(["export", csv_path], store_path)
    assert r.returncode == 0
    assert os.path.exists(csv_path)
    assert "Ship the report" in open(csv_path).read()


def test_delete_by_prefix(tmp_path):
    store_path = str(tmp_path / "events.json")
    run(["add", "2026-09-25", "work", "Ship the report"], store_path)
    r = run(["list"], store_path)
    event_id = r.stdout.split()[0]
    r = run(["delete", event_id], store_path)
    assert r.returncode == 0
    r = run(["list"], store_path)
    assert "no events" in r.stdout
