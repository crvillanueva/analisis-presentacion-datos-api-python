from __future__ import annotations

from datetime import date, timedelta
from typing import cast

import pandas as pd
import pydeck as pdk
import requests
import streamlit as st

from api import load_earthquakes


TODAY = date.today()
MIN_AVAILABLE_DATE = date(TODAY.year - 5, 1, 1)
DEFAULT_START_DATE = TODAY - timedelta(days=30)
DEFAULT_END_DATE = TODAY
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
            min_value=MIN_AVAILABLE_DATE,
            max_value=TODAY,
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

    map_data = df.copy()
    map_data["time_label"] = map_data["time"].dt.strftime("%Y-%m-%d %H:%M UTC")

    midpoint = (
        float(map_data["latitude"].mean()),
        float(map_data["longitude"].mean()),
    )

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_data,
        get_position="[longitude, latitude]",
        get_radius="marker_size * 1200",
        get_fill_color=[217, 95, 2, 170],
        get_line_color=[255, 255, 255],
        line_width_min_pixels=1,
        pickable=True,
        auto_highlight=True,
    )

    st.pydeck_chart(
        pdk.Deck(
            map_style=None,
            initial_view_state=pdk.ViewState(
                latitude=midpoint[0],
                longitude=midpoint[1],
                zoom=1,
                pitch=0,
            ),
            layers=[layer],
            tooltip={
                "html": (
                    "<b>{title}</b><br/>"
                    "Magnitude: {magnitude}<br/>"
                    "Depth: {depth_km} km<br/>"
                    "Time: {time_label}"
                ),
                "style": {
                    "backgroundColor": "#1f2937",
                    "color": "white",
                    "fontFamily": "sans-serif",
                },
            },
        ),
        use_container_width=True,
    )


def render_magnitude_depth_chart(df: pd.DataFrame) -> None:
    st.subheader("Magnitude vs Depth")
    if df.empty:
        return

    chart_data = df.dropna(subset=["magnitude", "depth_km"])
    if chart_data.empty:
        st.info("No events with depth data found for the selected filters.")
        return

    st.scatter_chart(
        chart_data,
        x="magnitude",
        y="depth_km",
        x_label="Magnitude",
        y_label="Depth (km)",
        color="#d95f02",
        size=80,
        height=420,
    )


def render_magnitude_event_count_chart(df: pd.DataFrame) -> None:
    st.subheader("Events by Magnitude")
    if df.empty:
        return

    chart_data = df.dropna(subset=["magnitude"])
    if chart_data.empty:
        st.info("No events with magnitude data found for the selected filters.")
        return

    lowest_magnitude = int(chart_data["magnitude"].min())
    highest_magnitude = int(chart_data["magnitude"].max()) + 1
    magnitude_edges = list(range(lowest_magnitude, highest_magnitude + 1))
    magnitude_labels = [
        f"{lower} <= M < {upper}"
        for lower, upper in zip(
            magnitude_edges[:-1], magnitude_edges[1:], strict=True
        )
    ]
    magnitude_ranges = pd.cut(
        chart_data["magnitude"],
        bins=magnitude_edges,
        labels=magnitude_labels,
        right=False,
    )
    event_counts = (
        magnitude_ranges.value_counts(sort=False)
        .rename_axis("Magnitude range")
        .reset_index(name="Events")
    )

    st.bar_chart(
        event_counts,
        x="Magnitude range",
        y="Events",
        x_label="Magnitude range",
        y_label="Events",
        color="#7570b3",
        sort=False,
        height=420,
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
    map_tab, magnitude_depth_tab, event_counts_tab, events_tab = st.tabs(
        ["Map", "Magnitude vs Depth", "Events by Magnitude", "Events"]
    )

    with map_tab:
        render_map(earthquakes)

    with magnitude_depth_tab:
        render_magnitude_depth_chart(earthquakes)

    with event_counts_tab:
        render_magnitude_event_count_chart(earthquakes)

    with events_tab:
        render_table(earthquakes)


if __name__ == "__main__":
    main()
