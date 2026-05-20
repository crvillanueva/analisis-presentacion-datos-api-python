from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd
import requests


USGS_EARTHQUAKE_API_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"


def fetch_earthquakes(
    start_date: date,
    end_date: date,
    min_magnitude: float,
) -> dict[str, Any]:
    """Fetch earthquake events from the USGS GeoJSON API."""
    if start_date > end_date:
        msg = "start_date must be before or equal to end_date"
        raise ValueError(msg)

    params: dict[str, str | float] = {
        "format": "geojson",
        "starttime": start_date.isoformat(),
        "endtime": end_date.isoformat(),
        "minmagnitude": min_magnitude,
    }

    response = requests.get(USGS_EARTHQUAKE_API_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def earthquakes_to_dataframe(payload: dict[str, Any]) -> pd.DataFrame:
    """Convert the USGS GeoJSON response to a flat dataframe for Streamlit."""
    rows: list[dict[str, Any]] = []

    for feature in payload.get("features", []):
        properties = feature.get("properties") or {}
        geometry = feature.get("geometry") or {}
        coordinates = geometry.get("coordinates") or [None, None, None]

        longitude = coordinates[0] if len(coordinates) > 0 else None
        latitude = coordinates[1] if len(coordinates) > 1 else None
        depth_km = coordinates[2] if len(coordinates) > 2 else None

        rows.append(
            {
                "id": feature.get("id"),
                "title": properties.get("title"),
                "place": properties.get("place"),
                "magnitude": properties.get("mag"),
                "mag_type": properties.get("magType"),
                "time": properties.get("time"),
                "updated": properties.get("updated"),
                "tsunami": properties.get("tsunami"),
                "alert": properties.get("alert"),
                "status": properties.get("status"),
                "event_type": properties.get("type"),
                "url": properties.get("url"),
                "longitude": longitude,
                "latitude": latitude,
                "depth_km": depth_km,
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df["time"] = pd.to_datetime(df["time"], unit="ms", utc=True)
    df["updated"] = pd.to_datetime(df["updated"], unit="ms", utc=True)
    numeric_columns = ["magnitude", "longitude", "latitude", "depth_km"]
    df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors="coerce")
    df = df.dropna(subset=["latitude", "longitude", "magnitude"])
    df["marker_size"] = (df["magnitude"] ** 3).round(1)

    return df.sort_values("time", ascending=False).reset_index(drop=True)


def load_earthquakes(
    start_date: date,
    end_date: date,
    min_magnitude: float,
) -> pd.DataFrame:
    """Fetch and prepare earthquake events for dashboard use."""
    payload = fetch_earthquakes(start_date, end_date, min_magnitude)
    return earthquakes_to_dataframe(payload)
