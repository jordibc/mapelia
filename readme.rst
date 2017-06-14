mapelia
=======

Convierte imágenes con mapas a ficheros 3D.

``mapelia`` es un programa para manipular ficheros de imágenes de mapas, en
proyección `de Mercator`_, `central cilíndrica`_ o `de Mollweide`_, y
convertirlos en `polígonos`_ o `puntos en el espacio`_ que pueden ser
manipulados por programas como `MeshLab`_ o `Blender`_.

.. _`de Mercator`: https://en.wikipedia.org/wiki/Mercator_projection
.. _`central cilíndrica`: https://en.wikipedia.org/wiki/Central_cylindrical_projection
.. _`de Mollweide`: https://en.wikipedia.org/wiki/Mollweide_projection
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
  Extracting heights from the image...
  The output is in file venus.ply

y obtenemos:

.. image:: examples/screenshot_meshlab.png


Uso
---

  usage: mapelia [-h] [-o OUTPUT] [--overwrite] [--type {ply,asc}]
                 [--channel {r,g,b,average,hue,sat,val,color}] [--invert]
                 [--projection {mercator,cylindrical,mollweide}]
                 [--points POINTS] [--scale SCALE] [--no-poles] [--no-meridian]
                 [--fix-gaps]
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
                          entrada) (default: None)
    --overwrite           no comprobar si el fichero de salida existe (default:
                          False)
    --type {ply,asc}      tipo de fichero a generar (default: ply)
    --channel {r,g,b,average,hue,sat,val,color}
                          canal que contiene la información de la elevación
                          (default: val)
    --invert              invierte las elevaciones (default: False)
    --projection {mercator,cylindrical,mollweide}
                          tipo de proyección usada en el mapa (default:
                          mercator)
    --points POINTS       número de puntos a usar como máximo (default: 500000)
    --scale SCALE         fracción de radio entre el punto más bajo y más alto
                          (default: 0.02)
    --no-poles            no añadir polos (default: False)
    --no-meridian         no añadir meridiano 0 (default: False)
    --fix-gaps            intenta rellenar los huecos en el mapa (default:
                          False)
  
    usage: mapelia [-h] [-o OUTPUT] [--overwrite] [--type {asc,ply}]
                   [--channel {r,g,b,hue,value}] [--invert]
                   [--projection {mercator,cylindrical}] [--points POINTS]
                   [--scale SCALE] [--no-poles] [--no-meridian] [--fix-gaps]
                   image


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
