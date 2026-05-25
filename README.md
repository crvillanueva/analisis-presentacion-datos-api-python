https://earthquake.usgs.gov/data/comcat/index.php#time -> Referencia de que significa cada campo de la
información entregada por la API de terremotos

This a dashboard to visualize earthquakes given the USGS earthquake API

# Earthquake API

The `https://earthquake.usgs.gov/fdsnws/event/1/query` API is used with the `requests` library to make the actually requests

As example:

```http
GET https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=2014-01-01&endtime=2014-01-02&minmagnitude=6

```


As examp

# Data processing

Pandas is used for loading and processing the data obtained from the API

# Visualizing

[streamlit](https://docs.streamlit.io/) is used as library for interactive visualization

There is a map where each point represents and event and where the size depends on the magnitude of the event.

Eventos que poseen alerta de tsunami podrían tener un emoji de ola 🌊

## Capabilities

You can filter by magnitud and date range

# Analysis



# Deployment

--
