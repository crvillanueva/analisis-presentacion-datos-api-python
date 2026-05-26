from datetime import date, timedelta
from typing import cast

import pandas as pd
import pydeck as pdk
import requests
import streamlit as st
from api import obtener_datos_terremotos

fecha_hoy = date.today()
fecha_minima_disponible = date(fecha_hoy.year - 5, 1, 1)
fecha_inicio_defecto = fecha_hoy - timedelta(days=30)
fecha_fin_defecto = fecha_hoy
magnitud_minima_defecto = 6.0


st.set_page_config(
    page_title="USGS Dashboard Terremotos",
    page_icon=":earth_americas:",
    layout="wide",
)


@st.cache_data(ttl=60 * 15, show_spinner=False)
def obtener_datos_terremotos_cacheados(
    fecha_inicio: date,
    fecha_fin: date,
    magnitud_min: float,
):
    return obtener_datos_terremotos(fecha_inicio, fecha_fin, magnitud_min)


def mostrar_filtros() -> tuple[date, date, float]:
    with st.sidebar:
        st.header("Filtros")
        fechas_seleccionadas = st.date_input(
            "Rango fecha",
            value=(fecha_inicio_defecto, fecha_fin_defecto),
            min_value=fecha_minima_disponible,
            max_value=fecha_hoy,
        )
        if isinstance(fechas_seleccionadas, tuple) and len(fechas_seleccionadas) == 2:
            fecha_inicio, fecha_fin = cast(tuple[date, date], fechas_seleccionadas)
        else:
            fecha_inicio = fecha_inicio_defecto
            fecha_fin = fecha_fin_defecto
            st.warning("Se debe seleccionar fecha inicio y fecha fin.")

        magnitud_minima = st.slider(
            "Magnitud mínima",
            min_value=0.0,
            max_value=10.0,
            value=magnitud_minima_defecto,
            step=0.1,
        )
        st.caption("Fuente de datos: USGS API")

    return fecha_inicio, fecha_fin, magnitud_minima


def mostrar_metricas(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("No se encontraron eventos para los filtros seleccionados.")
        return

    magnitud_max = df.loc[df["magnitude"].idxmax()]
    prof_max = df.loc[df["depth_km"].idxmax()]

    columna_total, columna_magnitud, columna_profundidad, columna_tsunami = st.columns(
        4
    )
    columna_total.metric(label="Eventos", value=f"{len(df):,}")
    columna_magnitud.metric(
        label="Magnitud máxima", value=f"M {magnitud_max['magnitude']:.1f}"
    )
    columna_profundidad.metric(
        label="Profundidad máxima", value=f"{prof_max['depth_km']:.0f} km"
    )
    columna_tsunami.metric(
        label="Alertas de tsunami", value=f"{int(df['tsunami'].sum()):,}"
    )


def graf_mapa(df: pd.DataFrame) -> None:
    st.subheader("Mapa terremotos")
    if df.empty:
        return

    df_mapa = df.copy()
    df_mapa["time_label"] = df_mapa["time"].dt.strftime("%Y-%m-%d %H:%M UTC")

    punto_medio = (
        float(df_mapa["latitude"].mean()),
        float(df_mapa["longitude"].mean()),
    )

    capa = pdk.Layer(
        "ScatterplotLayer",
        data=df_mapa,
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
                latitude=punto_medio[0],
                longitude=punto_medio[1],
                zoom=1,
                pitch=0,
            ),
            layers=[capa],
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


def renderizar_graf_magnitud_vs_prof(df: pd.DataFrame) -> None:
    st.subheader("Magnitud vs Profundidad")
    if df.empty:
        return

    df_grafico = df.dropna(subset=["magnitude", "depth_km"])
    if df_grafico.empty:
        st.info("Sin eventos con profundidad para los filtros seleccionados.")
        return

    st.scatter_chart(
        df_grafico,
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

    df_grafico = df.dropna(subset=["magnitude"])
    if df_grafico.empty:
        st.info("Sin eventos con datos de magnitud para los filtros seleccionados.")
        return

    magnitud_mas_baja = int(df_grafico["magnitude"].min())
    magnitud_mas_alta = int(df_grafico["magnitude"].max()) + 1
    magnitud_bordes = list(range(magnitud_mas_baja, magnitud_mas_alta + 1))
    magnitud_etiqueta = [
        f"{limite_inferior} <= M < {limite_superior}"
        for limite_inferior, limite_superior in zip(
            magnitud_bordes[:-1], magnitud_bordes[1:], strict=True
        )
    ]
    rangos_magnitud = pd.cut(
        df_grafico["magnitude"],
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

    tabla = df[
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
        tabla,
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
            df_terremotos = obtener_datos_terremotos_cacheados(
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

    mostrar_metricas(df_terremotos)
    tab_mapa, tab_magnitud_profundidad, tab_conteo_eventos, tab_eventos = st.tabs(
        ["Mapa", "Magnitud vs Profundidad", "N Eventos por magnitud", "Eventos"]
    )

    with tab_mapa:
        graf_mapa(df_terremotos)

    with tab_magnitud_profundidad:
        renderizar_graf_magnitud_vs_prof(df_terremotos)

    with tab_conteo_eventos:
        renderizar_graf_magnitud_vs_n_eventos(df_terremotos)

    with tab_eventos:
        graf_tabla(df_terremotos)


if __name__ == "__main__":
    main()
