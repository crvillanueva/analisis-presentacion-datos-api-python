from datetime import date

import pandas as pd
import requests


def obtener_datos_api_terremotos(
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

    url_api = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    parametros = {
        "format": "geojson",
        # necesario ya que la API usa fechas en formato (YYYY-MM-DD)
        "starttime": fecha_inicio.isoformat(),
        "endtime": fecha_fin.isoformat(),
        "minmagnitude": magnitud_min,
    }

    timeout_segundos = 30
    respuesta = requests.get(url_api, params=parametros, timeout=timeout_segundos)
    # 200 = OK
    if respuesta.status_code != 200:
        msg_error = f"Error al obtener datos de la API: {respuesta.status_code} - {respuesta.text}"
        raise Exception(msg_error)
    return respuesta.json()


def terremotos_a_dataframe(datos_api):
    """Convierte la respuesta de la API a un DataFrame."""

    filas = []
    for evento in datos_api.get("features", []):
        propiedades = evento.get("properties") or {}
        geometria = evento.get("geometry") or {}
        coordenadas = geometria.get("coordinates") or [None, None, None]

        longitud = coordenadas[0] if len(coordenadas) > 0 else None
        latitud = coordenadas[1] if len(coordenadas) > 1 else None
        profundidad_km = coordenadas[2] if len(coordenadas) > 2 else None

        filas.append(
            {
                "id": evento.get("id"),
                "title": propiedades.get("title"),
                "place": propiedades.get("place"),
                "magnitude": propiedades.get("mag"),
                "mag_type": propiedades.get("magType"),
                "time": propiedades.get("time"),
                "updated": propiedades.get("updated"),
                "tsunami": propiedades.get("tsunami"),
                "alert": propiedades.get("alert"),
                "status": propiedades.get("status"),
                "event_type": propiedades.get("type"),
                "url": propiedades.get("url"),
                "longitude": longitud,
                "latitude": latitud,
                "depth_km": profundidad_km,
            }
        )

    df = pd.DataFrame(filas)
    if df.empty:
        return df

    df["time"] = pd.to_datetime(df["time"], unit="ms", utc=True)
    df["updated"] = pd.to_datetime(df["updated"], unit="ms", utc=True)
    columnas_numericas = ["magnitude", "longitude", "latitude", "depth_km"]
    df[columnas_numericas] = df[columnas_numericas].apply(
        pd.to_numeric, errors="coerce"
    )
    df = df.dropna(subset=["latitude", "longitude", "magnitude"])
    # nueva columna para el tamaño de los marcadores en el mapa, basada en la magnitud
    df["marker_size"] = (df["magnitude"] ** 3).round(1)

    return df.sort_values("time", ascending=False).reset_index(drop=True)


def obtener_datos_terremotos(
    fecha_inicio: date,
    fecha_fin: date,
    magnitud_min: float,
) -> pd.DataFrame:
    """Obtener y preparar los eventos desde la API para uso por el dashboard."""
    datos_api = obtener_datos_api_terremotos(fecha_inicio, fecha_fin, magnitud_min)
    return terremotos_a_dataframe(datos_api)
