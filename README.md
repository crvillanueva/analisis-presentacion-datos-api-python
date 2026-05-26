# Análisis y presentación de datos utilizando API en Python

En este proyecto se visualizan de manera geoespacial e interactiva los eventos de terremotos
del mundo a partir de un catálogo de datos puesto a disposición por la USGS (_United States Geological Survey_)
consumido a través de una REST API que responde a llamadas web.

El proyecto integra un mapa donde se disponen los eventos como puntos escalados según su magnitud.
Ademas de gráficos para visualizar relaciones entre la magnitud y otras variables como la profundidad
o el numero de eventos en rangos de tiempos y magnitud filtrables e interactivos.

Todo esto con el objetivo de responder las preguntas: ¿Dónde se ubican geográficamente los terremotos?
¿Existe alguna relación entre el número de eventos o la profundidad y su magnitud?

## Proceso

El proceso para la visualización y análisis desde los datos crudos
consiste de maneral generalizada en:

1. Interacción con servicio externo para obtención de datos
2. Transformación de los datos a estructuras de datos/objetos trabajables por Python para y análisis
3. Visualización interactiva


### Interacción con servicio externo para obtención de datos

Los datos provienen desde la API `https://earthquake.usgs.gov/fdsnws/event/1/query` la cual permite
la parametrización de la fecha de inicio, fin y magnitud mínima de los eventos solicitados,
existen además otros parámetros no usados en la dashboard propiamente tal; para mayor información
revisar la [documentación oficial de la API](https://earthquake.usgs.gov/fdsnws/event/1/#parameters).

De este modo una _request_ como:

```http
https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=2014-01-01&endtime=2014-01-02&minmagnitude=6
```

Entrega un resultado como:

```json
{
  "type": "FeatureCollection",
  "metadata": {
    "generated": 1779766060000,
    "url": "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=2014-01-01&endtime=2014-01-02&minmagnitude=6",
    "title": "USGS Earthquakes",
    "status": 200,
    "api": "2.4.0",
    "count": 1
  },
  "features": [
    {
      "type": "Feature",
      "properties": {
        "mag": 6.5,
        "place": "32 km W of Sola, Vanuatu",
        "time": 1388592209000,
        "updated": 1651596180609,
        "tz": null,
        "url": "https://earthquake.usgs.gov/earthquakes/eventpage/usc000lvb5",
        "detail": "https://earthquake.usgs.gov/fdsnws/event/1/query?eventid=usc000lvb5&format=geojson",
        "felt": null,
        "cdi": null,
        "mmi": 4.262,
        "alert": "green",
        "status": "reviewed",
        "tsunami": 1,
        "sig": 650,
        "net": "us",
        "code": "c000lvb5",
        "ids": ",pt14001000,at00myqcls,usc000lvb5,iscgem604060577,",
        "sources": ",pt,at,us,iscgem,",
        "types": ",cap,impact-link,losspager,moment-tensor,origin,phase-data,shakemap,",
        "nst": null,
        "dmin": 3.997,
        "rms": 0.76,
        "gap": 14,
        "magType": "mww",
        "type": "earthquake",
        "title": "M 6.5 - 32 km W of Sola, Vanuatu"
      },
      "geometry": {
        "type": "Point",
        "coordinates": [
          167.249,
          -13.8633,
          187
        ]
      },
      "id": "usc000lvb5"
    }
  ]
}
```

En el código la interacción se implementa con la biblioteca
[`requests`](https://requests.readthedocs.io/). En `code/api.py`, la función
`obtener_datos_api_terremotos` define los parámetros de búsqueda y ejecuta la llamada
HTTP con `requests.get`:

```python
parametros = {
    "format": "geojson",
    "starttime": fecha_inicio.isoformat(),
    "endtime": fecha_fin.isoformat(),
    "minmagnitude": magnitud_min,
}

respuesta = requests.get(url_api, params=parametros, timeout=timeout_segundos)
```

Luego se valida que la API responda con estado `200` y se retorna el contenido
como JSON usando `respuesta.json()`, para que pueda ser transformado y analizado
por el resto de la aplicación.

## Analisis de los datos

El análisis de datos se realiza principalmente con
[`pandas`](https://pandas.pydata.org/), que permite convertir la respuesta JSON
de la API en una tabla trabajable por Python.

En `code/api.py`, la función `terremotos_a_dataframe` recorre los eventos del
campo `features`, extrae sus propiedades principales y crea un `DataFrame`:

```python
df = pd.DataFrame(filas)
```

Después se normalizan los datos para que sean útiles en la visualización:

- `pd.to_datetime` convierte las fechas entregadas por la API en milisegundos a
  fechas UTC.
- `pd.to_numeric` transforma columnas como magnitud, latitud, longitud y
  profundidad a valores numéricos.
- `dropna` elimina eventos sin coordenadas o sin magnitud.
- `sort_values` ordena los eventos desde el más reciente.
- `marker_size` se calcula desde la magnitud para escalar los puntos del mapa.

Un caso concreto de análisis está en `code/dashboard.py`, donde se determina el
número de eventos para cada rango de magnitud. Primero se agrupan las magnitudes
en intervalos con `pd.cut` y luego se cuentan los eventos de cada intervalo con
`value_counts`:

```python
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
```

El resultado es una tabla con dos columnas: el rango de magnitud y el número de
eventos encontrados en ese rango. Esta tabla es la que después se usa para
construir el gráfico de barras de eventos por magnitud.

## Visualización interactiva

La visualización se construye con la ayuda de
[`streamlit`](https://docs.streamlit.io/), biblioteca que cumple el rol central en
`code/dashboard.py`.

_Streamlit_ se usa para definir la página, los filtros, las métricas, las pestañas
y los componentes visuales de la dashboard.

En particular _Streamlit_ posee widgets ya construidos que permiten el rápido
desarrollo de aplicaciones web, entre los elementos usados en esta aplicación:

- `st.sidebar` contiene los filtros de rango de fecha y magnitud mínima.
- `st.metric` muestra indicadores como total de eventos, magnitud máxima,
  profundidad máxima y alertas de tsunami.
- `st.tabs` separa las vistas de mapa, gráfico de magnitud/profundidad, eventos
  por magnitud y tabla de eventos.
- `st.pydeck_chart` muestra los terremotos en un mapa interactivo.
- `st.scatter_chart` muestra la relación entre magnitud y profundidad.
- `st.bar_chart` visualiza el número de eventos por rango de magnitud.
- `st.dataframe` presenta el detalle tabular de los eventos.

`st.pydeck_chart` fue requerido sobre la versión mas simple de `st.map` (https://docs.streamlit.io/develop/api-reference/charts/st.map) ya que esta no poseía la funcionalidad de un _hover_ personalizado.

De esta manera, al modificar los filtros de fecha o magnitud, Streamlit vuelve a
ejecutar la consulta, procesa los datos y actualiza las visualizaciones.
interactiva.

## Código

### Estructura de los archivos del proyecto

```
code/ -> Carpeta que contiene todo el código necesario para ejecutar la aplicación
code/api.py -> Logica asociada al consumo de datos desde la API
code/dashboard.py -> Visualización e interacción de los datos obtenidos
requirements.txt -> Listado de librerías necesarias para poder ejecutar el proyecto
README.md -> Documentación principal del proyecto
aprendizajes.md -> Documentación dedicada a nuevos conceptos aprendidos
```

El código vive en `code/api.py` y `code/dashboard.py`

### Ejecución local

Los siguientes corresponden a los comandos a ingresar en la terminal/consola para poder
ejecutar la aplicación de manera local.

1. Instalar las bibliotecas necesarias para correr la aplicación:

```bash
pip install -r requirements.txt
```

*Nota: Considerar que el proyecto se desarrollo en `Python 3.14`.
Otras versiones podrían no ser compatibles con las versiones de las
librerías de este proyecto

2. Ejecutar el servidor de la aplicación streamlit:

```
streamlit run code/dashboard.py --server.port 8091
```

3. Abrir el navegador en `http://localhost:8091`

*Nota: El valor del puerto (_server.port_) es configurable.
