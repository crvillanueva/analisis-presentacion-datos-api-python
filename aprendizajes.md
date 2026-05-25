# Análisis y presentación de datos utilizando API en Python

## Aprendizajes

### Requests HTTP

Para obtener los datos fue necesario "llamar" servicios externos (en particular la API de la USGS),
en el proceso fue necesario comprender conceptos como:

### Requests y responses

Una _request_ es un mensaje, petición o llamada enviada a un servidor;
una _response_ por otro lado es la _respuesta_ del server.

#### Métodos de petición HTTP

Cuando se solicita un recurso se debe indicar el tipo de acción. Por ej. `POST` para enviar
una entidad a un recurso específico, o `GET` para solicitar una representación de un recurso;
este método fue usado en el proyecto para "solitar" la información desde la api mediante la
biblioteca _requests_ con `requests.get(url)`.

### Códigos de estado de respuesta HTTP

Los códigos de estado de respuesta HTTP indican si se ha completado satisfactoriamente una solicitud HTTP específica.
Algunos comunes como `200 OK` o `404 Not Found` pueden indicar si la solicitud fue exitosa o erronéa.
Para el caso de la aplicación fue necesario determinar si la _request_ hasta la API de la USGS se llevo a cabo
correctamente y así poder determinar si el servicio se encuentra funcionando correctamente.

### Query parameters

Las URLs (en este caso la API solicitada) puede poseer _query parameters_.
En el proyecto en particular se uso para determinar el formato y los filtros
necesarios para la interactividad de la dashboard.

```
https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=2014-01-01&endtime=2014-01-02
```

Y en el código:

```python
# ...
params = {
    "format": "geojson",
    "starttime": start_date.isoformat(),
    "endtime": end_date.isoformat(),
    "minmagnitude": min_magnitude,
}
# ...
response = requests.get(api_url, params=params, timeout=timeout_seconds)
```

### Formatos de texto

Existen `JSON`, debido a que JSON es un formato extendido la librería _requests_ posee
métodos exclusivos como `response.json()` para transformar los datos en este formato
a un objecto nativo de _Python_ representado por un diccionario.

### Lectura de documentación

La sección de solicitudes web requirío la lectura de páginas como [la documentación de Mozilla](https://developer.mozilla.org/es/docs/Web/HTTP/Reference/Status)
para comprender los conceptos usados en el código.

Por otro lado en la escritura del código se requirío el uso de bibliotecas externas como
`streamlit`, `pandas` y `requests`, cada una de estas bibliotecas poseen sus propias
funcionalidades y convenciones, es por esto que fue necesario aprender a leer y navegar
su documentación mediante la exploración de los links:

- https://docs.streamlit.io/: Documentación de streamlit, usada para chequear los posibles _widgets_ disponibles
para la visualización web y para la forma de desplegar la aplicación.
- https://requests.readthedocs.io/en/latest/: Comprender las funcionalidades como: setear
el método HTTP a realizar, paso de _query parameters_ a partir de un diccionario
- https://pandas.pydata.org/docs/: Usado para determinar

### git y Github

El despliegue de la aplicación nativo de streamlit requería una cuenta en [Github](https://github.com/).
Este proceso involucró subir el código del proyecto hasta un "repositorio" online.
Github requiere a su vez la existencia de un "repositorio" de git, el cual corresponde
a un popular sistema de control de versiones. Para la creación de esto fue necesario
la instalación de git y la ejecución de los comandos:

```
git init
```

```
git remote add <github_repo_link>
```

```
git push
```

En Github se creo además un archivo `README.md` correspondiente a un archivo que es mostrado
directamente en el link del repositorio y que generalmente srive como documentación.

## Referencias

- https://developer.mozilla.org/es/docs/Web/HTTP/Reference/Methods
- https://developer.mozilla.org/es/docs/Web/HTTP/Reference/Status
- https://developer.mozilla.org/en-US/docs/Web/URI/Reference/Query
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app
