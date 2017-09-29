mapelia y amigos
================

Este repositorio contiene un grupo de programas relacionados con convertir
imágenes con mapas a ficheros 3D.

* ``mapelia`` - convierte mapas en figuras 3D con relieves
* ``guapelia`` - GUI opcional para usar mapelia
* ``pintelia`` - convierte mapas en figuras 3D coloreadas
* ``poligoniza`` - forma caras (polígonos) a partir de los puntos 3D
* ``stl-split`` - divide un globo 3D en hemisferios norte y sur

Los mapas son imágenes ``jpg`` o ``png`` y pueden estar en proyección
`equirectangular`_, `de Mercator`_, `central cilíndrica`_, `de Mollweide`_
o `sinusoidal`_.

.. _`equirectangular`: https://en.wikipedia.org/wiki/Equirectangular_projection
.. _`de Mercator`: https://en.wikipedia.org/wiki/Mercator_projection
.. _`central cilíndrica`: https://en.wikipedia.org/wiki/Central_cylindrical_projection
.. _`de Mollweide`: https://en.wikipedia.org/wiki/Mollweide_projection
.. _`sinusoidal`: https://en.wikipedia.org/wiki/Sinusoidal_projection

El resultado de los programas son ficheros 3D (de polígonos como `ply`_ o
`stl`_, o puntos en el espacio como `asc`_), que pueden ser visualizados y
manipulados por programas como `MeshLab`_ o `Blender`_.

.. _`ply`: https://en.wikipedia.org/wiki/PLY_(file_format)
.. _`stl`: https://en.wikipedia.org/wiki/STL_(file_format)
.. _`asc`: https://codeyarns.com/2011/08/17/asc-file-format-for-3d-points/
.. _`MeshLab`: https://en.wikipedia.org/wiki/MeshLab
.. _`Blender`: https://www.blender.org/


mapelia
=======

``mapelia`` es un programa para manipular ficheros de imágenes de mapas, y
convertirlos en figuras 3D con los relieves extraídos del mapa.

Ejemplo
-------

Empezando con la siguiente imagen:

.. image:: examples/venus.png

ejecutamos::

  $ ./mapelia examples/venus.png
  Processing file examples/venus.png ...
  - Extracting heights from image (channel "val")...
  Adding north cap...
  - Forming faces...
  Adding map...
  - Projecting heights on a sphere...
  - Forming faces...
  Stitching patches...
  - Forming faces...
  Adding south cap...
  - Forming faces...
  Stitching patches...
  - Forming faces...
  The output is in file examples/venus.ply

y obtenemos:

.. image:: examples/screenshot_meshlab.png

Uso
---

  usage: mapelia [-h] [-o OUTPUT] [--overwrite] [--type {ply,asc,stl}]
                 [--channel {r,g,b,average,hue,sat,val,color}] [--invert]
                 [--projection {mercator,central-cylindrical,mollweide,equirectangular,sinusoidal}]
                 [--points POINTS] [--scale SCALE] [--caps CAPS]
                 [--logo-north LOGO_NORTH] [--logo-south LOGO_SOUTH]
                 [--no-meridian] [--protrusion PROTRUSION] [--no-ratio-check]
                 [--fix-gaps]
                 image

  Convierte imágenes con mapas a ficheros 3D. Toma mapas de ficheros jpg, png,
  etc., y escribe ficheros ply (polígonos), asc (nube de puntos) o stl (también
  polígonos) con una esfera que contiene las elevaciones deducidas del mapa en
  cada punto. Estos ficheros se pueden a su vez manipular con programas como
  MeshLab o Blender.

  positional arguments:
    image                 fichero de imagen con el mapa

  optional arguments:
    -h, --help            show this help message and exit
    -o OUTPUT, --output OUTPUT
                          fichero de salida (si vacío, se genera a partir del de
                          entrada) (default: )
    --overwrite           no comprobar si el fichero de salida existe (default:
                          False)
    --type ply_asc_stl    tipo de fichero a generar (default: ply)
    --channel r_g_b_average_hue_sat_val_color
                          canal que contiene la información de la elevación
                          (default: val)
    --invert              invierte las elevaciones (default: False)
    --projection mercator_central-cylindrical_mollweide_equirectangular_sinusoidal
                          tipo de proyección usada en el mapa (default:
                          mercator)
    --points POINTS       número de puntos a usar como máximo (o 0 para usar
                          todos) (default: 0)
    --scale SCALE         fracción de radio entre el punto más bajo y más alto
                          (default: 0.02)
    --caps CAPS           ángulo (en grados) al que llegan los casquetes (o auto
                          o none) (default: auto)
    --logo-north LOGO_NORTH
                          fichero de imagen con el logo norte (default: )
    --logo-south LOGO_SOUTH
                          fichero de imagen con el logo sur (default: )
    --meridian MERIDIAN   longitud (en grados) donde colocar el meridiano (o
                          none) (default: 0)
    --protrusion PROTRUSION
                          fracción en la que sobresalen meridiano y casquetes
                          del máximo (default: 1.02)
    --no-ratio-check      no arreglar el ratio alto/ancho en ciertas
                          proyecciones (default: False)
    --fix-gaps            intenta rellenar los huecos en el mapa (default:
                          False)

pintelia
========

Ejemplo
-------

Ejecutando::

  $ ./pintelia examples/earth_equirectangular.jpg --proj equirectangular
  Processing file examples/earth_equirectangular.jpg ...
  - Forming faces...
  The output is in file examples/earth_equirectangular.ply

obtenemos:

.. image:: examples/screenshot_meshlab_pintelia.png


Uso
---

  usage: pintelia [-h] [-o OUTPUT] [--overwrite]
                  [--projection {mercator,cylindrical,mollweide,equirectangular,sinusoidal}]
                  [--points POINTS] [--no-ratio-check] [--fix-gaps]
                  image

  Pinta en colores sobre la superficie de una esfera una imagen con un mapa.
  Toma mapas de ficheros jpg, png, etc., y escribe ficheros ply (polígonos).

  positional arguments:
    image                 fichero de imagen con el mapa

  optional arguments:
    -h, --help            show this help message and exit
    -o OUTPUT, --output OUTPUT
                          fichero de salida (si vacío, se genera a partir del de
                          entrada) (default: )
    --overwrite           no comprobar si el fichero de salida existe (default:
                          False)
    --projection mercator_central-cylindrical_mollweide_equirectangular_sinusoidal
                          tipo de proyección usada en el mapa (default:
                          mercator)
    --points POINTS       número de puntos a usar como máximo (o 0 para usar
                          todos) (default: 0)
    --no-ratio-check      no arreglar el ratio alto/ancho en ciertas
                          proyecciones (default: False)
    --fix-gaps            intenta rellenar los huecos en el mapa (default:
                          False)
