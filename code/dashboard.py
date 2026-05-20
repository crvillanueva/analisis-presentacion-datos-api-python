from __future__ import annotations

from datetime import date, timedelta
from typing import cast

import pandas as pd
import requests
import streamlit as st

from api import load_earthquakes


DEFAULT_START_DATE = date(2014, 1, 1)
DEFAULT_END_DATE = date(2014, 1, 2)
DEFAULT_MIN_MAGNITUDE = 6.0


st.set_page_config(
    page_title="USGS Earthquake Dashboard",
    page_icon=":earth_americas:",
    layout="wide",
)


@st.cache_data(ttl=60 * 15, show_spinner=False)
def cached_load_earthquakes(
    start_date: date,
    end_date: date,
    min_magnitude: float,
) -> pd.DataFrame:
    return load_earthquakes(start_date, end_date, min_magnitude)


def render_filters() -> tuple[date, date, float]:
    with st.sidebar:
        st.header("Filters")
        selected_dates = st.date_input(
            "Date range",
            value=(DEFAULT_START_DATE, DEFAULT_END_DATE),
            max_value=date.today() + timedelta(days=1),
        )

        if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
            start_date, end_date = cast(tuple[date, date], selected_dates)
        else:
            start_date = DEFAULT_START_DATE
            end_date = DEFAULT_END_DATE
            st.warning("Select a start and end date.")

        min_magnitude = st.slider(
            "Minimum magnitude",
            min_value=0.0,
            max_value=10.0,
            value=DEFAULT_MIN_MAGNITUDE,
            step=0.1,
        )

        st.caption("Data source: USGS Earthquake Catalog API")

    return start_date, end_date, min_magnitude


def render_metrics(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("No earthquake events found for the selected filters.")
        return

    strongest_event = df.loc[df["magnitude"].idxmax()]
    deepest_event = df.loc[df["depth_km"].idxmax()]

    total_events, strongest, deepest, tsunami_events = st.columns(4)
    total_events.metric("Events", f"{len(df):,}")
    strongest.metric("Strongest", f"M {strongest_event['magnitude']:.1f}")
    deepest.metric("Deepest", f"{deepest_event['depth_km']:.0f} km")
    tsunami_events.metric("Tsunami alerts", f"{int(df['tsunami'].sum()):,}")


def render_map(df: pd.DataFrame) -> None:
    st.subheader("Earthquake Map")
    if df.empty:
        return

    st.map(
        df,
        latitude="latitude",
        longitude="longitude",
        size="marker_size",
        color="#d95f02",
        use_container_width=True,
    )


def render_table(df: pd.DataFrame) -> None:
    st.subheader("Events")
    if df.empty:
        return

    table = df[
        [
            "time",
            "magnitude",
            "place",
            "depth_km",
            "alert",
            "tsunami",
            "status",
            "url",
        ]
    ].rename(
        columns={
            "time": "Time UTC",
            "magnitude": "Magnitude",
            "place": "Place",
            "depth_km": "Depth km",
            "alert": "Alert",
            "tsunami": "Tsunami",
            "status": "Status",
            "url": "USGS URL",
        }
    )

    st.dataframe(
        table,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Time UTC": st.column_config.DatetimeColumn(format="YYYY-MM-DD HH:mm"),
            "Magnitude": st.column_config.NumberColumn(format="%.1f"),
            "Depth km": st.column_config.NumberColumn(format="%.1f"),
            "Tsunami": st.column_config.CheckboxColumn(),
            "USGS URL": st.column_config.LinkColumn(display_text="Open event"),
        },
    )


def main() -> None:
    st.title("USGS Earthquake Dashboard")
    st.write(
        "Visualize earthquake events from the USGS API with date and magnitude filters."
    )

    start_date, end_date, min_magnitude = render_filters()

    if start_date > end_date:
        st.error("The start date must be before or equal to the end date.")
        return

    try:
        with st.spinner("Loading earthquake events..."):
            earthquakes = cached_load_earthquakes(
                start_date=start_date,
                end_date=end_date,
                min_magnitude=min_magnitude,
            )
    except requests.HTTPError as exc:
        st.error(f"The USGS API returned an error: {exc}")
        return
    except requests.RequestException as exc:
        st.error(f"Could not connect to the USGS API: {exc}")
        return
    except ValueError as exc:
        st.error(str(exc))
        return

    render_metrics(earthquakes)
    render_map(earthquakes)
    render_table(earthquakes)


if __name__ == "__main__":
    main()
