from datetime import date, timedelta
from typing import cast

import pandas as pd
import pydeck as pdk
import requests
import streamlit as st
from api import obtener_data_terremotos

fecha_hoy = date.today()
fecha_minima_disponible = date(fecha_hoy.year - 5, 1, 1)
fecha_inicio_defautl = fecha_hoy - timedelta(days=30)
fecha_fin_default = fecha_hoy
magnitud_minima_default = 6.0


st.set_page_config(
    page_title="USGS Dashboard Terremotos",
    page_icon=":earth_americas:",
    layout="wide",
)


@st.cache_data(ttl=60 * 15, show_spinner=False)
def cache_obtener_data_terremotos(
    fecha_inicio: date,
    fecha_fin: date,
    magnitud_min: float,
):
    return obtener_data_terremotos(fecha_inicio, fecha_fin, magnitud_min)


def mostrar_filtros() -> tuple[date, date, float]:
    with st.sidebar:
        st.header("Filtros")
        selected_dates = st.date_input(
            "Rango fecha",
            value=(fecha_inicio_defautl, fecha_fin_default),
            min_value=fecha_minima_disponible,
            max_value=fecha_hoy,
        )
        if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
            fecha_inicio, fecha_fin = cast(tuple[date, date], selected_dates)
        else:
            fecha_inicio = fecha_inicio_defautl
            fecha_fin = fecha_fin_default
            st.warning("Se debe seleccionar fecha inicio y fecha fin.")

        min_magnitude = st.slider(
            "Magnitud mínima",
            min_value=0.0,
            max_value=10.0,
            value=magnitud_minima_default,
            step=0.1,
        )
        st.caption("Fuente de datos: USGS API")

    return fecha_inicio, fecha_fin, min_magnitude


def mostrar_metricas(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("No se encontraron eventos para los filtros seleccionados.")
        return

    magnitud_max = df.loc[df["magnitude"].idxmax()]
    prof_max = df.loc[df["depth_km"].idxmax()]

    total_events, strongest, deepest, tsunami_events = st.columns(4)
    total_events.metric(label="Eventos", value=f"{len(df):,}")
    strongest.metric(
        label="Magnitud máxima", value=f"M {magnitud_max['magnitude']:.1f}"
    )
    deepest.metric(label="Profundidad máxima", value=f"{prof_max['depth_km']:.0f} km")
    tsunami_events.metric(
        label="Alertas de tsunami", value=f"{int(df['tsunami'].sum()):,}"
    )


def graf_mapa(df: pd.DataFrame) -> None:
    st.subheader("Mapa terremotos")
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
                    "Magnitud: {magnitude}<br/>"
                    "Profundidad: {depth_km} km<br/>"
                    "Fecha: {time_label}"
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


def renderizar_graf_magnitud_vs_prof(df) -> None:
    st.subheader("Magnitud vs Profundidad")
    if df.empty:
        return

    chart_data = df.dropna(subset=["magnitude", "depth_km"])
    if chart_data.empty:
        st.info("Sin eventos con profundidad para los filtros seleccionados.")
        return

    st.scatter_chart(
        chart_data,
        x="magnitude",
        y="depth_km",
        x_label="Magnitud",
        y_label="Profundidad (km)",
        color="#d95f02",
        size=80,
        height=420,
    )


def renderizar_graf_magnitud_vs_n_eventos(df: pd.DataFrame) -> None:
    st.subheader("N Eventos por magnitud")
    if df.empty:
        return

    chart_data = df.dropna(subset=["magnitude"])
    if chart_data.empty:
        st.info("Sin eventos con datos de magnitud para los filtros seleccionados.")
        return

    magnitud_mas_baja = int(chart_data["magnitude"].min())
    magnitud_mas_alta = int(chart_data["magnitude"].max()) + 1
    magnitud_bordes = list(range(magnitud_mas_baja, magnitud_mas_alta + 1))
    magnitud_etiqueta = [
        f"{lower} <= M < {upper}"
        for lower, upper in zip(magnitud_bordes[:-1], magnitud_bordes[1:], strict=True)
    ]
    rangos_magnitud = pd.cut(
        chart_data["magnitude"],
        bins=magnitud_bordes,
        labels=magnitud_etiqueta,
        right=False,
    )
    n_eventos = (
        rangos_magnitud.value_counts(sort=False)
        .rename_axis("Magnitude range")
        .reset_index(name="Events")
    )

    st.bar_chart(
        n_eventos,
        x="Magnitude range",
        y="Events",
        x_label="Rango magnitud",
        y_label="Eventos",
        color="#7570b3",
        sort=False,
        height=420,
    )


def graf_tabla(df: pd.DataFrame) -> None:
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
    st.title("Dashboard Terremotos USGS")
    st.write(
        "Visualización de eventos desde la API de la USGS con filtros de fecha y magnitud."
    )

    fecha_inicio, fecha_fin, magnitud_min = mostrar_filtros()

    if fecha_inicio > fecha_fin:
        st.error("La fecha de inicio debe ser anterior a la fecha de fin.")
        return

    try:
        with st.spinner("Cargando eventos..."):
            earthquakes = cache_obtener_data_terremotos(
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                magnitud_min=magnitud_min,
            )
    except requests.HTTPError as exc:
        st.error(f"La API entregó un error: {exc}")
        return
    except requests.RequestException as exc:
        st.error(f"No fue posible conectarse a la API: {exc}")
        return
    except ValueError as exc:
        st.error(str(exc))
        return

    mostrar_metricas(earthquakes)
    map_tab, magnitude_depth_tab, event_counts_tab, events_tab = st.tabs(
        ["Mapa", "Magnitud vs Profundidad", "N Eventos por magnitud", "Eventos"]
    )

    with map_tab:
        graf_mapa(earthquakes)

    with magnitude_depth_tab:
        renderizar_graf_magnitud_vs_prof(earthquakes)

    with event_counts_tab:
        renderizar_graf_magnitud_vs_n_eventos(earthquakes)

    with events_tab:
        graf_tabla(earthquakes)


if __name__ == "__main__":
    main()
