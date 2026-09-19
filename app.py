"""
app.py — Streamlit event calendar.

Same storage.EventStore as calendar_cli.py: add/delete/search with the
same validation, a Plotly heatmap of the current month with day numbers
laid over it, a bar chart of events per month, category counts, a
"next 7 days" panel, and CSV export.

Run with:  streamlit run app.py
"""
import calendar as cal
import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

import plotly.graph_objects as go
import streamlit as st

from storage import EventStore, CATEGORIES, ValidationError

STORE_PATH = os.environ.get("CALENDAR_STORE", "events.json")
CAT_CODE = {c: i + 1 for i, c in enumerate(CATEGORIES)}  # 0 = empty
CAT_COLOUR = {"work": "#3b6fe0", "personal": "#37b26c", "study": "#a15fd6", "urgent": "#d64545"}
COLORSCALE = [
    (0.0, "#eef0f3"), (0.2, "#eef0f3"),
    (0.2, CAT_COLOUR["work"]), (0.4, CAT_COLOUR["work"]),
    (0.4, CAT_COLOUR["personal"]), (0.6, CAT_COLOUR["personal"]),
    (0.6, CAT_COLOUR["study"]), (0.8, CAT_COLOUR["study"]),
    (0.8, CAT_COLOUR["urgent"]), (1.0, CAT_COLOUR["urgent"]),
]

st.set_page_config(page_title="Event calendar", page_icon="\U0001F4C5", layout="wide")


def get_store():
    if "store" not in st.session_state:
        st.session_state.store = EventStore(STORE_PATH)
    return st.session_state.store


store = get_store()

if "view_year" not in st.session_state:
    today = date.today()
    st.session_state.view_year = today.year
    st.session_state.view_month = today.month

st.title("Event calendar")
st.caption("Built twice on purpose: calendar_cli.py first to get the storage and validation right, "
           "then this Streamlit view once the logic held. Same JSON store either way.")

# ---------------- sidebar: add / delete / search ----------------
with st.sidebar:
    st.header("Add event")
    with st.form("add_event", clear_on_submit=True):
        d = st.date_input("Date", value=date.today(), key="add_date")
        cat = st.selectbox("Category", CATEGORIES, key="add_category")
        desc = st.text_input("Description", key="add_description")
        submitted = st.form_submit_button("Add")
        if submitted:
            try:
                store.add(d.isoformat(), cat, desc)
                st.success(f"Added {d.isoformat()} · {cat}")
            except ValidationError as e:
                st.error(str(e))

    st.divider()
    st.header("Delete event")
    all_sorted = sorted(store.events, key=lambda e: e.date)
    if all_sorted:
        options = {f"{e.date} · {e.category} · {e.description} ({e.id[:8]})": e.id for e in all_sorted}
        pick = st.selectbox("Pick an event", list(options.keys()), key="delete_pick")
        if st.button("Delete selected", key="delete_button"):
            if store.delete(options[pick]):
                st.success("Deleted.")
                st.rerun()
    else:
        st.caption("No events yet.")

    st.divider()
    st.header("Search")
    query = st.text_input("Description, date, or category", key="search_query")

# ---------------- month navigation ----------------
nav_l, nav_mid, nav_r, nav_clear = st.columns([1, 3, 1, 2])
with nav_l:
    if st.button("← Prev", key="nav_prev"):
        m, y = st.session_state.view_month - 1, st.session_state.view_year
        if m < 1:
            m, y = 12, y - 1
        st.session_state.view_month, st.session_state.view_year = m, y
with nav_r:
    if st.button("Next →", key="nav_next"):
        m, y = st.session_state.view_month + 1, st.session_state.view_year
        if m > 12:
            m, y = 1, y + 1
        st.session_state.view_month, st.session_state.view_year = m, y
with nav_mid:
    st.subheader(f"{cal.month_name[st.session_state.view_month]} {st.session_state.view_year}")
with nav_clear:
    if st.button("Clear all events", key="clear_all"):
        for e in list(store.events):
            store.delete(e.id)
        st.rerun()

year, month = st.session_state.view_year, st.session_state.view_month
month_events = store.by_month(year, month)
events_by_day = {}
for e in month_events:
    events_by_day.setdefault(e.date, []).append(e)

# ---------------- month grid (Plotly heatmap, Monday-first) ----------------
weeks = cal.monthcalendar(year, month)  # Monday-first, like the stdlib
z, text, hover = [], [], []
today_iso = date.today().isoformat()
for week in weeks:
    zrow, trow, hrow = [], [], []
    for day in week:
        if day == 0:
            zrow.append(0)
            trow.append("")
            hrow.append("")
            continue
        iso = f"{year:04d}-{month:02d}-{day:02d}"
        evs = events_by_day.get(iso, [])
        code = CAT_CODE[evs[0].category] if evs else 0
        zrow.append(code)
        marker = " ●" if iso == today_iso else ""
        label = f"{day}{marker}"
        if evs:
            label += f"<br>{evs[0].category}" + (f" (+{len(evs)-1})" if len(evs) > 1 else "")
        trow.append(label)
        hrow.append("<br>".join(f"{e.category}: {e.description}" for e in evs) or "no events")
    z.append(zrow)
    text.append(trow)
    hover.append(hrow)

fig = go.Figure(data=go.Heatmap(
    z=z, text=text, texttemplate="%{text}", textfont={"size": 12},
    customdata=hover, hovertemplate="%{customdata}<extra></extra>",
    colorscale=COLORSCALE, zmin=0, zmax=4, showscale=False,
    xgap=3, ygap=3,
))
fig.update_yaxes(autorange="reversed", showticklabels=False)
fig.update_xaxes(
    tickmode="array", tickvals=list(range(7)),
    ticktext=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], side="top",
)
fig.update_layout(height=280 + 40 * len(weeks), margin=dict(l=10, r=10, t=40, b=10))

left, right = st.columns([3, 1])
with left:
    st.plotly_chart(fig, width='stretch')

    counts = store.counts_by_category()
    st.markdown(" · ".join(f":blue[{c}] **{n}**" if c == "work" else f"{c} **{n}**"
                                 for c, n in counts.items()))

with right:
    st.markdown("**Next 7 days**")
    upcoming = store.next_n_days(7)
    if upcoming:
        for e in upcoming:
            st.markdown(f"`{e.date}` **{e.category}** — {e.description}")
    else:
        st.caption("Nothing scheduled.")

# ---------------- search results ----------------
if query:
    st.divider()
    st.markdown(f"**Search results for “{query}”**")
    results = store.search(query)
    if results:
        st.dataframe(
            [{"date": e.date, "category": e.category, "description": e.description} for e in results],
            width='stretch', hide_index=True,
        )
    else:
        st.caption("No matches.")

# ---------------- events per month + export ----------------
st.divider()
by_month = store.counts_by_month()
if by_month:
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown("**Events per month**")
        st.bar_chart(by_month)
    with c2:
        st.markdown("**Export**")
        st.metric("Total events", len(store.events))
        tmp_path = "_export.csv"
        store.to_csv(tmp_path)
        with open(tmp_path, "rb") as f:
            st.download_button("Download CSV", f, file_name="events.csv", mime="text/csv")
else:
    st.caption("No events yet — add one from the sidebar.")
