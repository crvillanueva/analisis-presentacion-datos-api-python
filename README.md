# Análisis y presentación de datos utilizando API en Python

En este proyecto se visualizan de manera geoespacial e interactiva los eventos de terremotos
del mundo mediante un catálogo de datos puesto a disposición por la USGS (_United States Geological Survey_)
consumido a través de una REST API que responde a llamadas web.

El proyecto integra un mapa donde se disponen los eventos como puntos escalados según su magnitud.
Ademas de gráficos para visualizar relaciones entre la magnitud y otras variables como la profundidad
o el numero de eventos en rangos de tiempos y magnitud filtrables e interactivos.

Todo esto con el objetivo de responder las preguntas: ¿Dónde se ubican geograficamente los terremotos?
¿Existe alguna relación entre el numero de eventos o la profundidad y su magnitud?

El proceso involucra a grandes rasgos las fases:

1. Interacción con servicio externo para obtención de datos
2. Transformación de los datos a estructuras de datos/objectos trabajables por Python para su análisis
3. Visualización de los datos de manera interactiva


## Interacción con servicio externo para obtención de datos

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


## Código

### Estructura de los archivos del proyecto

```
code/ -> Carpeta que contiene todo el código necesario para ejecutar la aplicación
code/api.py -> Logica asociada al consumo de datos desde la API
code/dashboard.py -> Visualización e interacción de los datos obtenidos
requirements.txt -> Librerias necesarias para poder ejecutar el proyecto
README.md -> Documentación principal del proyecto
docs/aprendizajes.md -> Documentación dedicada a nuevos conceptos aprendidos
```

El código vive en `code/api.py` y `code/dashboard.py`

### Ejecución local

Los siguientes corresponden a los comandos a ingresar en la terminal/consola para poder
ejecutar la aplicación de manera local.

1. Instalar las bibliotecas necesarias para correr la aplicación:

```bash
pip install -r requirements.txt
```

2. Ejecutar el servidor de la aplicación streamlit:

```
streamlit run code/dashboard.py --server.port 8091
```

3. Abrir el navegador en `http://localhost:8091`

*Nota: El valor del puerto (_server.port_) es configurable.
