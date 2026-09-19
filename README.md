<div align="center">

# Event Calendar

<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&size=22&duration=2800&pause=900&color=2F6FED&center=true&vCenter=true&width=700&lines=One+JSON+store%2C+two+interfaces.;Plan+the+week+from+the+terminal+or+the+browser.;Small+enough+to+read.+Useful+enough+to+keep." alt="Typing animation with project taglines" /></a>

<p>
	<img src="https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white" alt="Python 3.9 or newer" />
	<img src="https://img.shields.io/badge/Streamlit-app-FF4B4B?logo=streamlit&logoColor=white" alt="Streamlit app" />
	<img src="https://img.shields.io/badge/Storage-JSON-333333?logo=json&logoColor=white" alt="JSON storage" />
	<img src="https://img.shields.io/badge/License-MIT-2EA44F" alt="MIT license" />
</p>

**A small event calendar with a terminal CLI, a Streamlit dashboard, and one shared data model.**

</div>

> **The useful bit:** add an event in the CLI, refresh the dashboard, and it is already there. Both interfaces read and write the same human-readable `events.json` file.

> **Demo placeholder:** Add a short GIF or screenshot here showing the monthly heatmap and one CLI command. Suggested path: `docs/assets/event-calendar-demo.gif`.

## Why this project exists

This project was built in two passes. The CLI came first, which forced the data model, validation, and persistence to work without a UI covering for them. The Streamlit app sits on that same core.

That makes the project easy to inspect and easy to extend: change the store once, then use the behavior from either interface.

## Features

- [x] Add, delete, list, search, and export events from the terminal
- [x] View a Monday-first month grid in Streamlit
- [x] Use four categories: `work`, `personal`, `study`, and `urgent`
- [x] Validate dates, descriptions, and categories before saving
- [x] Skip malformed rows instead of failing the entire load
- [x] See category counts, upcoming events, and events per month
- [x] Export the full calendar as CSV
- [ ] Add recurring events and reminders

## Quick start

### 1. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 2. Start the dashboard

```bash
streamlit run app.py
```

The app opens with the current month. Add events from the sidebar, navigate month by month, or search by description, date, or category.

### 3. Try the CLI

```bash
python calendar_cli.py add 2026-09-25 work "Ship the Q3 report"
python calendar_cli.py list --month 2026-09
python calendar_cli.py search report
python calendar_cli.py stats
python calendar_cli.py export events.csv
```

Delete an event with its full ID or an unambiguous prefix:

```bash
python calendar_cli.py delete a1b2c3d4
```

<details>
<summary><strong>Use a different data file</strong></summary>

The CLI defaults to `events.json` in the current directory. Pass `--store` before the subcommand to use another file:

```bash
python calendar_cli.py --store data/team-events.json add 2026-09-25 work "Ship the Q3 report"
```

For Streamlit, set `CALENDAR_STORE` before starting the app:

```bash
# macOS/Linux
CALENDAR_STORE=data/team-events.json streamlit run app.py

# PowerShell
$env:CALENDAR_STORE = "data/team-events.json"
streamlit run app.py
```

</details>

## How it works

`src/storage.py` owns the rules and file access. Every write is persisted immediately. When the store loads data, it validates each row and ignores bad rows such as an invalid date, unknown category, or blank description.

The dashboard uses Plotly for the month heatmap and the monthly event chart. The CLI and Streamlit app do not maintain separate data paths, so behavior stays consistent between them.

<details>
<summary><strong>Repository map</strong></summary>

```text
app.py                Streamlit UI: calendar, search, charts, and CSV export
calendar_cli.py       CLI: add, delete, list, search, stats, and export
src/storage.py        Shared EventStore, validation, persistence, and queries
tests/test_storage.py Unit tests for the store
tests/test_cli.py     End-to-end tests for CLI commands
```

</details>

## Run the tests

```bash
python -m pytest tests/ -v
```

The test suite covers validation, persistence, malformed-row skipping, corrupt-file recovery, search, month filtering, counts, upcoming events, CSV export, and CLI subprocess behavior.

## API at a glance

<details>
<summary><strong>CLI commands</strong></summary>

| Command | Purpose |
| --- | --- |
| `add YYYY-MM-DD CATEGORY DESCRIPTION` | Save a new event |
| `delete ID_OR_PREFIX` | Delete one uniquely matched event |
| `list [--month YYYY-MM]` | List all events or one month |
| `search QUERY` | Search description, date, or category |
| `stats` | Show category totals and the next seven days |
| `export PATH` | Write all events to CSV |

</details>

## License

MIT. See [LICENSE](LICENSE).
