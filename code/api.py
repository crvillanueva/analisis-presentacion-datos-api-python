from datetime import date

import pandas as pd
import requests


def get_api_data_terremotos(
    fecha_inicio: date,
    fecha_fin: date,
    magnitud_min: float,
):
    """Obtiene datos de terremotos desde la API de USGS en formato JSON."""

    if fecha_inicio > fecha_fin:
        msg_error = (
            "Error: La fecha de inicio no puede ser posterior a la fecha de fin."
        )
        raise ValueError(msg_error)

    api_url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "geojson",
        # necesario ya que la API usa fechas en formato (YYYY-MM-DD)
        "starttime": fecha_inicio.isoformat(),
        "endtime": fecha_fin.isoformat(),
        "minmagnitude": magnitud_min,
    }

    timeout_seconds = 30
    response = requests.get(api_url, params=params, timeout=timeout_seconds)
    # 200 = OK
    if response.status_code != 200:
        msg_error = f"Error al obtener datos de la API: {response.status_code} - {response.text}"
        raise Exception(msg_error)
    return response.json()


def terremotos_a_dataframe(payload):
    """Convierte la response de la API a un DataFrame."""

    filas = []
    for feature in payload.get("features", []):
        properties = feature.get("properties") or {}
        geometry = feature.get("geometry") or {}
        coordinates = geometry.get("coordinates") or [None, None, None]

        longitude = coordinates[0] if len(coordinates) > 0 else None
        latitude = coordinates[1] if len(coordinates) > 1 else None
        depth_km = coordinates[2] if len(coordinates) > 2 else None

        filas.append(
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

    df = pd.DataFrame(filas)
    if df.empty:
        return df

    df["time"] = pd.to_datetime(df["time"], unit="ms", utc=True)
    df["updated"] = pd.to_datetime(df["updated"], unit="ms", utc=True)
    numeric_columns = ["magnitude", "longitude", "latitude", "depth_km"]
    df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors="coerce")
    df = df.dropna(subset=["latitude", "longitude", "magnitude"])
    # nueva columna para el tamaño de los marcadores en el mapa, basada en la magnitud
    df["marker_size"] = (df["magnitude"] ** 3).round(1)

    return df.sort_values("time", ascending=False).reset_index(drop=True)


def obtener_data_terremotos(
    fecha_inicio: date,
    fecha_fin: date,
    magnitud_min: float,
) -> pd.DataFrame:
    """Obtener y preparar los eventos desde la API para uso por la dashboard."""
    payload = get_api_data_terremotos(fecha_inicio, fecha_fin, magnitud_min)
    return terremotos_a_dataframe(payload)
