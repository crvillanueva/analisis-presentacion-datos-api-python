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

### Calidad de Codigo

Durante el desarrollo también fue importante aplicar prácticas que mejoran la legibilidad,
mantención y revisión del código.

#### Sistema de `typing`

Python permite agregar anotaciones de tipo para indicar qué valores espera una función.
Esto no cambia directamente la ejecución del programa, pero ayuda a entender el código,
detectar errores antes y usar mejor las ayudas del editor.

Un ejemplo está en la función `get_api_data_terremotos` de `code/api.py`:

```python
def get_api_data_terremotos(
    fecha_inicio: date,
    fecha_fin: date,
    magnitud_min: float,
):
```

En este caso, las anotaciones indican que `fecha_inicio` y `fecha_fin` deben ser fechas
(`date`), mientras que `magnitud_min` debe ser un número decimal (`float`). Con esto es
más fácil comprender cómo llamar la función sin tener que revisar todo su contenido.

#### Separación de código en archivos

Otra mejora de calidad fue separar responsabilidades en archivos distintos. El archivo
`code/api.py` contiene la lógica para llamar la API de USGS y transformar la respuesta en
datos utilizables por la aplicación. En cambio, `code/dashboard.py` contiene la lógica de
interfaz, filtros, métricas, gráficos y tabla de Streamlit.

Esta separación permite que cada archivo tenga un objetivo claro: si se necesita cambiar
cómo se obtienen los datos, se revisa `code/api.py`; si se necesita cambiar cómo se muestran
los datos, se revisa `code/dashboard.py`.

#### Nombres representativos

Los nombres de variables y funciones también aportan a la calidad del código. Nombres como
`fecha_inicio`, `fecha_fin`, `magnitud_min`, `obtener_data_terremotos`, `mostrar_filtros`
y `renderizar_graf_magnitud_vs_n_eventos` comunican la intención del código sin depender
solo de comentarios.

Esto mejora la legibilidad porque permite leer el programa como una secuencia de acciones:
obtener datos, mostrar filtros, calcular métricas y renderizar gráficos. Mientras más claro
es el nombre, menos esfuerzo se necesita para entender qué hace cada parte.

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

Estos comandos fueron indicados directamente luego de crear un nuevo repositorio en GitHub.

En Github se creo además un archivo `README.md` correspondiente a un archivo que es mostrado
directamente en el link del repositorio y que generalmente srive como documentación.

## Referencias

- https://developer.mozilla.org/es/docs/Web/HTTP/Reference/Methods
- https://developer.mozilla.org/es/docs/Web/HTTP/Reference/Status
- https://developer.mozilla.org/en-US/docs/Web/URI/Reference/Query
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app
