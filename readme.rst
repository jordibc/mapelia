mapelia
=======

Convierte imágenes con mapas a ficheros 3D.

``mapelia`` es un programa para manipular ficheros de imágenes de mapas, y
convertirlos en `polígonos`_ o `puntos en el espacio`_ que pueden ser
manipulados por programas como `MeshLab`_ o `Blender`_.

Los mapas pueden estar en proyección `equirectangular`_, `de Mercator`_,
`central cilíndrica`_, `de Mollweide`_ o `sinusoidal`_.

.. _`equirectangular`: https://en.wikipedia.org/wiki/Equirectangular_projection
.. _`de Mercator`: https://en.wikipedia.org/wiki/Mercator_projection
.. _`central cilíndrica`: https://en.wikipedia.org/wiki/Central_cylindrical_projection
.. _`de Mollweide`: https://en.wikipedia.org/wiki/Mollweide_projection
.. _`sinusoidal`: https://en.wikipedia.org/wiki/Sinusoidal_projection
.. _`polígonos`: https://en.wikipedia.org/wiki/PLY_(file_format)
.. _`puntos en el espacio`: https://codeyarns.com/2011/08/17/asc-file-format-for-3d-points/
.. _`MeshLab`: https://en.wikipedia.org/wiki/MeshLab
.. _`Blender`: https://www.blender.org/


Ejemplo
-------

Empezando con la siguiente imagen:

.. image:: examples/venus.png

ejecutamos::

  $ mapelia venus.png
  Processing file venus.png ...
  - Extracting heights from the image...
  - Projecting heights on a sphere...
  - Forming the faces...
  The output is in file venus.ply

y obtenemos:

.. image:: examples/screenshot_meshlab.png


Uso
---

  usage: mapelia [-h] [-o OUTPUT] [--overwrite] [--type {ply,asc}]
                 [--channel {r,g,b,average,hue,sat,val,color}] [--invert]
                 [--projection {mercator,cylindrical,mollweide,equirectangular,sinusoidal}]
                 [--points POINTS] [--scale SCALE] [--caps CAPS] [--no-meridian]
                 [--protrusion PROTRUSION] [--no-ratio-check] [--fix-gaps]
                 image

  Convierte imágenes con mapas a ficheros 3D. Toma mapas en proyección de
  Mercator, cónica o de Mollweide, de ficheros jpg, png, etc., y escribe
  ficheros ply (polígonos) o asc (nube de puntos) con una esfera que contiene
  las elevaciones deducidas del mapa en cada punto. Estos ficheros se pueden a
  su vez manipular con programas como MeshLab o Blender.

  positional arguments:
    image                 fichero de imagen con el mapa

  optional arguments:
    -h, --help            show this help message and exit
    -o OUTPUT, --output OUTPUT
                          fichero de salida (si vacío, se genera a partir del de
                          entrada) (default: )
    --overwrite           no comprobar si el fichero de salida existe (default:
                          False)
    --type ply_asc        tipo de fichero a generar (default: ply)
    --channel r_g_b_average_hue_sat_val_color
                          canal que contiene la información de la elevación
                          (default: val)
    --invert              invierte las elevaciones (default: False)
    --projection mercator_cylindrical_mollweide_equirectangular_sinusoidal
                          tipo de proyección usada en el mapa (default:
                          mercator)
    --points POINTS       número de puntos a usar como máximo (default: 500000)
    --scale SCALE         fracción de radio entre el punto más bajo y más alto
                          (default: 0.02)
    --caps CAPS           ángulo (en grados) al que llegan los casquetes (o auto
                          o none) (default: auto)
    --no-meridian         no añadir meridiano 0 (default: False)
    --protrusion PROTRUSION
                          fracción en la que sobresalen meridiano y casquetes
                          del máximo (default: 1.2)
    --no-ratio-check      no arreglar el ratio alto/ancho en ciertas
                          proyecciones (default: False)
    --fix-gaps            intenta rellenar los huecos en el mapa (default:
                          False)


Procesamiento con MeshLab
-------------------------

Una forma posible de continuar importando un fichero asc en meshlab:

* Filters -> Sampling (tercero por abajo) -> Poisson-disk Sampling (a
  la mitad) ; number of samples: 100000, con opción: Base Mesh
  Subsampling.
* Filters -> Normals, curvature and orientation -> Compute normals for
  pointsets ; neigbors: 20.
* Filters -> Point set -> Marching cubes (APSS) ; Grid resolution: 1000.
* Filters -> Cleaning and Repairing -> Simplification MC: Edge Collapse.
* Exportar a stl.


Procesamiento con Blender
-------------------------

Una forma posible de continuar procesando el asc desde blender:

* Con meshlab: exportar el asc como ply.
* Importar con blender el nuevo ply.
* Crear una "ico sphere" con 8 subdivisiones.
* Escalar la esfera para que tenga un tamaño parecido a la nube de puntos.
* Usar el modifier "shrinkwrap", poniendo como target la nube de puntos, y como modo "nearest vertex".
* Exportar el resultado como ply.


Mapas
-----

Datasets que se pueden considerar para Venus:

* https://sos.noaa.gov/Datasets/dataset.php?id=218
* http://www.maps-of-the-world.net/maps/space-maps/maps-of-venus/large-detailed-satellite-map-of-Venus.jpg
* http://stevealbers.net/albers/sos/venus/venuscyl5.jpg
* https://astrogeology.usgs.gov/search/map/Venus/Magellan/RadarProperties/Venus_Magellan_Topography_Global_4641m

Datos de Magallanes
~~~~~~~~~~~~~~~~~~~

Para extraer elevaciones (radios planetarios) de latitudes y
longitudes específicas en Venus, ir a:

http://ode.rsl.wustl.edu/venus/pagehelp/quickstartguide/index.html?mgn_rdrs_gxdr.htm

y ver el contenido de la sección “GTDR” (la 4ª desde arriba). Se
pueden bajar los datos en 4 proyecciones distintas desde:

http://pds-geosciences.wustl.edu/mgn/mgn-v-gxdr-v1/mg_3002/gsdr/


Mejoras
-------

Para el futuro querría:

* Añadir un interfaz gráfico decente.
* Barra de progreso mientras escribe el fichero.
* Hacer un preview de las imágenes de los mapas cuando se seleccionan.
* Presentar estadísticas de desviación típica, componentes de Fourier y
  similares, según el canal elegido para extraer la elevación.
* Añadir un modo de selección de canal automático, según lo que parece más
  prometedor por las estadísticas de la imagen.
* Permitir abrir el resultado en meshlab o en blender si están disponibles.
* Documentar el algoritmo que he escrito para conectar los puntos en triángulos
  de la esfera.
