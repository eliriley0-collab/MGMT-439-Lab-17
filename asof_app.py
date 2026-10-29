"""Run: python -m streamlit run asof_app.py"""
from datetime import date
from io import StringIO
import re

import numpy as np
import pandas as pd
import requests
import streamlit as st

SERIES = {
    "BAA": "Moody's Baa corporate bond yield",
    "FEDFUNDS": "Federal funds rate",
    "DGS10": "10-year Treasury yield",
    "MORTGAGE30US": "30-year mortgage rate",
}


def read_csv(url, params):
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    frame = pd.read_csv(StringIO(response.text), na_values=["."])
    if len(frame.columns) != 2 or frame.columns[0].lower() not in ("date", "observation_date"):
        raise ValueError("The server did not return a two-column observation CSV.")
    dates = pd.to_datetime(frame.iloc[:, 0], errors="raise")
    values = pd.to_numeric(frame.iloc[:, 1], errors="raise")
    result = pd.Series(values.to_numpy(), index=dates, name=params["id"]).sort_index()
    if result.index.has_duplicates:
        raise ValueError("Duplicate observation dates in download.")
    return result


@st.cache_data(ttl=3600, show_spinner=False)
def download_today(series_id, download_day):
    """download_day makes the cache expire across calendar days too."""
    return read_csv("https://fred.stlouisfed.org/graph/fredgraph.csv", {"id": series_id})


@st.cache_data(ttl=3600, show_spinner=False)
def download_asof(series_id, vintage_date, download_day):
    """Ask ALFRED for the vintage, never truncate today's revised series."""
    values = read_csv(
        "https://alfred.stlouisfed.org/graph/alfredgraph.csv",
        {"id": series_id, "vintage_date": vintage_date.isoformat()},
    )
    # Observation dates describe the measured period, not its publication date.
    # The vintage request above is what enforces historical availability.
    return values.loc[values.index <= pd.Timestamp(vintage_date)]


def compare(current, historical):
    current, historical = current.dropna(), historical.dropna()
    last_then = historical.index.max() if not historical.empty else pd.NaT
    common = pd.concat([historical, current], axis=1, keys=["then", "today"]).dropna()
    revised = int((~np.isclose(common["then"], common["today"], rtol=0, atol=1e-9)).sum())
    return {
        "Last measured date known then": last_then,
        "Value known then": historical.iloc[-1] if not historical.empty else None,
        "Last measured date today": current.index.max() if not current.empty else pd.NaT,
        "Value today": current.iloc[-1] if not current.empty else None,
        "Later observations today": int((current.index > last_then).sum()) if pd.notna(last_then) else len(current),
        "Revised shared observations": revised,
    }


def main():
    st.set_page_config(page_title="Point-in-Time Rates Audit", layout="wide")
    today = date.today()
    st.title("Point-in-Time Rates Audit")
    st.caption(f"Data from FRED and ALFRED, Federal Reserve Bank of St. Louis, downloaded {today}; built with AI help, a learning demonstration, not investment advice.")
    st.markdown("[FRED](https://fred.stlouisfed.org/) · [ALFRED](https://alfred.stlouisfed.org/)")
    selected = st.sidebar.multiselect("Series", list(SERIES), default=list(SERIES), format_func=lambda s: f"{s} — {SERIES[s]}")
    extra = st.sidebar.text_input("Add a FRED series ID", placeholder="PAYEMS").strip().upper()
    if extra and extra not in selected:
        if re.fullmatch(r"[A-Z0-9_]+", extra):
            selected.append(extra)
        else:
            st.sidebar.error("Use a series ID containing letters, digits, or underscores.")
    start = st.sidebar.date_input("Chart start date", date(2020, 1, 1), min_value=date(1776, 1, 1), max_value=today)
    vintage = st.sidebar.date_input("As known on", today, min_value=date(1776, 1, 1), max_value=today)
    st.caption("Counts cover all downloaded history. Missing observations (.) are excluded; no values are filled. Monthly dates label the measured month. A daily vintage does not establish availability before an intraday trade.")
    rows = []
    for series_id in selected:
        st.subheader(f"{series_id} — {SERIES.get(series_id, 'Additional series')}")
        try:
            current = download_today(series_id, today)
            st.line_chart(current.loc[current.index >= pd.Timestamp(start)])
        except Exception as error:
            st.error(f"{series_id}: current download failed: {error}")
            continue
        try:
            historical = download_asof(series_id, vintage, today)
            result = compare(current, historical)
            last = result["Last measured date known then"]
            st.write(f"Last measured date known on {vintage}: {last.date() if pd.notna(last) else 'No nonmissing observations available'}")
            rows.append({"Series": f"https://fred.stlouisfed.org/series/{series_id}", **result})
            with st.expander(f"Inspect {series_id} vintages / download audit data"):
                audit = pd.concat([historical, current], axis=1, keys=["Known then", "Today"])
                st.dataframe(audit.sort_index(ascending=False))
                st.download_button("Download comparison CSV", audit.to_csv(), f"{series_id}_{vintage}_audit.csv", key=series_id)
        except Exception as error:
            st.error(f"{series_id}: historical download failed: {error}. No current values substituted.")
    st.subheader("Availability and revisions")
    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True, column_config={"Series": st.column_config.LinkColumn("Series", display_text=r".*/series/(.*)")})
    else:
        st.info("Select a series with available downloads to see the audit table.")


if __name__ == "__main__":
    main()
