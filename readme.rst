mapelia and friends
===================

This repository has several programs related to images of maps and 3D files.

* ``mapelia`` -- convert maps into 3D figures with reliefs.
* ``guapelia`` -- optional GUI to use mapelia.
* ``pintelia`` -- convert maps into colored 3D figures.
* ``poligoniza`` -- form faces (polygons) from 3D points.
* ``stl-split`` -- split a 3D glove into the north and south hemispheres.

The maps are ``jpg`` or ``png`` images and can have as projections
`equirectangular`_, `Mercator`_, `central cylindrical`_, `Mollweide`_
or `sinusoidal`_.

.. _`equirectangular`: https://en.wikipedia.org/wiki/Equirectangular_projection
.. _`Mercator`: https://en.wikipedia.org/wiki/Mercator_projection
.. _`central cilíndrica`: https://en.wikipedia.org/wiki/Central_cylindrical_projection
.. _`Mollweide`: https://en.wikipedia.org/wiki/Mollweide_projection
.. _`sinusoidal`: https://en.wikipedia.org/wiki/Sinusoidal_projection

The output of the programs are 3D files (of polygons like `ply`_ or
`stl`_, or points in space like `asc`_), that can be visualized and
manipulated with programs like `MeshLab`_ or `Blender`_.

.. _`ply`: https://en.wikipedia.org/wiki/PLY_(file_format)
.. _`stl`: https://en.wikipedia.org/wiki/STL_(file_format)
.. _`asc`: https://codeyarns.com/2011/08/17/asc-file-format-for-3d-points/
.. _`MeshLab`: https://en.wikipedia.org/wiki/MeshLab
.. _`Blender`: https://www.blender.org/


Installing
==========

The first time that you download this repository, you'll need to run::

  $ python3 setup.py build_ext --inplace

so as to generate the `projections` module from `projections.c`. Trying to
run directly `mapelia` will warn about the need to run this.

If you want to modify the file `projections.pyx`, you'll need to run then::

  $ cython3 -a projections.pyx

to regenerate the file `projections.c`.

mapelia
=======

``mapelia`` is a program to manipulate files with map images and
transform them into 3D figures with their heights extracted from the
map.

Example
-------

Starting with the following image:

.. image:: examples/venus.png

we run::

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

and get:

.. image:: examples/screenshot_meshlab.png

Usage
-----

  usage: mapelia [-h] [--output OUTPUT] [--overwrite] [--type {ply,asc,stl}]
                 [--channel {r,g,b,average,hue,sat,val,color}] [--invert]
                 [--projection {mercator,central-cylindrical,mollweide,equirectangular,sinusoidal}]
                 [--points POINTS] [--scale SCALE] [--caps CAPS]
                 [--caps-height CAPS_HEIGHT] [--logo-north LOGO_NORTH]
                 [--logo-north-scale LOGO_NORTH_SCALE] [--logo-south LOGO_SOUTH]
                 [--logo-south-scale LOGO_SOUTH_SCALE]
                 [--meridians-pos [POSITION [POSITION ...]]]
                 [--meridians-widths [WIDTH [WIDTH ...]]]
                 [--meridians-height MERIDIANS_HEIGHT] [--thickness THICKNESS]
                 [--no-ratio-check] [--blur BLUR] [--fix-gaps] [--config CONFIG]
                 image

  Transform images with maps into 3D files. It takes maps images in jpg, png and
  so on, and writes 3D polygon files (ply and stl) or clouds of 3D points (asc)
  with a sphere that contains the elevations deduced from the map at each point.
  These files can be further processed with programs like MeshLab or Blender.

  positional arguments:
    image                 image file with the map

  optional arguments:
    -h, --help            show this help message and exit
    --output OUTPUT       output file (if empty, it is generated from the image
                          file name) (default: )
    --overwrite           do not check if the output file already exists
                          (default: False)
    --type ply_asc_stl    type of 3D file to generate (default: ply)
    --channel r_g_b_average_hue_sat_val_color
                          channel with the elevations information in the image
                          (default: val)
    --invert              invert heights (default: False)
    --projection mercator_central-cylindrical_mollweide_equirectangular_sinusoidal
                          projection used in the map (default: mercator)
    --points POINTS       maximum number of points to use (or 0 to use all in
                          the image) (default: 0)
    --scale SCALE         fraction of radius between the highest and lowest
                          points (default: 0.02)
    --caps CAPS           angle (in degrees) where the caps end (or auto or
                          none) (default: auto)
    --caps-height CAPS_HEIGHT
                          height of the caps (1 would be at sea-level) (default:
                          1.02)
    --logo-north LOGO_NORTH
                          image file with the north logo (default: )
    --logo-north-scale LOGO_NORTH_SCALE
                          scale factor for the north logo (can be < 0 for
                          engravings) (default: 1.0)
    --logo-south LOGO_SOUTH
                          image file with the south logo (default: )
    --logo-south-scale LOGO_SOUTH_SCALE
                          scale factor for the south logo (can be < 0 for
                          engravings) (default: 1.0)
    --meridians-pos POSITION1_POSITION2_etc
                          list of longitudes (in degrees) with meridians
                          (default: [0])
    --meridians-widths WIDTH1_WIDTH2_etc
                          list of widths (in degrees) of the meridians (default:
                          [2])
    --meridians-height MERIDIANS_HEIGHT
                          elevation of the meridians (at the equator) (default:
                          1.02)
    --thickness THICKNESS
                          thickness of the generated object (< 1 for partially
                          hollow)) (default: 1)
    --no-ratio-check      do not fix the height/width ratio for certain
                          projections (default: False)
    --blur BLUR           amount of pixels used to smooth the image (default: 0)
    --fix-gaps            try to fill the gaps in the map (default: False)
    --config CONFIG       file with default parameters (default: )


pintelia
========

``pintelia`` es un programa para proyectar mapas en esferas 3D con los colores
originales del mapa.

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


poligoniza
==========

``poligoniza`` coge ficheros de puntos 3D (``.asc``) e intenta unirlos formando
las caras de un sólido.

Los puntos en el fichero original tienen que estar en cierto orden para que
queden bien las caras. Por ejemplo, el orden en que ``mapelia`` genera los
puntos (cuando no proyecta logos también).

Ejemplo
-------

::

  $ ./poligoniza ficheros_amelia/venus-out-12new.asc --type stl --invert
  Processing file ficheros_amelia/venus-out-12new.asc ...
  - Forming faces...
  The output is in file ficheros_amelia/venus-out-12new.stl

Uso
---

  usage: poligoniza [-h] [-o OUTPUT] [--overwrite] [--type {ply,stl}] [--ascii]
                    [--invert] [--row-length ROW_LENGTH]
                    file

  Crea un fichero de polígonos (.ply o .stl) a partir de uno con sólo los puntos
  (.asc). El fichero asc original debe tener los puntos en orden correspondiente
  a las secciones de un objeto casi-esférico.

  positional arguments:
    file                  fichero asc con las coordenadas de los puntos

  optional arguments:
    -h, --help            show this help message and exit
    -o OUTPUT, --output OUTPUT
                          fichero de salida (si vacío, se genera a partir del de
                          entrada) (default: )
    --overwrite           no comprobar si el fichero de salida existe (default:
                          False)
    --type ply_stl        tipo de fichero a generar (default: ply)
    --ascii               escribe el ply resultante en ascii (default: False)
    --invert              invierte la orientación de las caras (default: False)
    --row-length ROW_LENGTH
                          número de puntos por sección (si 0, se autodetecta)
                          (default: 0)


stl-split
=========

Divide un stl en casquete norte y casquete sur.

Ejemplo
-------

::

  $ ./stl-split mars.stl
  Processing file mars.stl ...
  Writing file mars_N.stl ...
  Writing file mars_S.stl ...

Uso
---

  usage: stl-split [-h] [-n NAME] [--number NUMBER] [--overwrite]
                   [--ignore-check]
                   file

  Divide un fichero stl. La idea es ayudar a post-procesar ficheros stl hechos
  con mapelia, para que se puedan imprimir más fácilmente. El fichero original
  no se modifica, sino que se crean dos nuevos ficheros acabados en "_N.stl" y
  "_S.stl" (o "_head.stl" y "_tail.stl" si se usa la opción --number).

  positional arguments:
    file                  fichero stl

  optional arguments:
    -h, --help            show this help message and exit
    -n NAME, --name NAME  nombre de salida (si vacío, se genera a partir del de
                          entrada) (default: )
    --number NUMBER       separar dejando el número dado de triángulos en el
                          primero (default: 0)
    --overwrite           no comprobar si los ficheros de salida existen
                          (default: False)
    --ignore-check        forzar el procesado del fichero aunque no parezca un
                          stl (default: False)


Posibles post-procesados
========================

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


Material de referencia
======================

Mapas
-----

* `Finding and Using Space Image Data`_
* `Planetary Data System`_

.. _`Finding and Using Space Image Data`: http://www.planetary.org/explore/space-topics/space-imaging/data.html
.. _`Planetary Data System`: https://en.wikipedia.org/wiki/Planetary_Data_System

Proyecciones
------------

* `Equirectangular`_
* `De Mercator`_
* `Central cilíndrica`_
* `De Mollweide`_
* `Sinusoidal`_

.. _`Equirectangular`: https://en.wikipedia.org/wiki/Equirectangular_projection
.. _`De Mercator`: https://en.wikipedia.org/wiki/Mercator_projection
.. _`Central cilíndrica`: https://en.wikipedia.org/wiki/Central_cylindrical_projection
.. _`De Mollweide`: https://en.wikipedia.org/wiki/Mollweide_projection
.. _`Sinusoidal`: https://en.wikipedia.org/wiki/Sinusoidal_projection

Formatos
--------

* `ply`_ -- "polígonos" en 3D, también admite colores
* `stl`_ -- "estereolitografía", triángulos en 3D, más cutre que ``ply`` pero muy usado para imprimir en 3D
* `asc`_ -- sólo puntos 3D

.. _`ply`: https://en.wikipedia.org/wiki/PLY_(file_format)
.. _`stl`: https://en.wikipedia.org/wiki/STL_(file_format)
.. _`asc`: https://codeyarns.com/2011/08/17/asc-file-format-for-3d-points/

Procesado
---------

* `Pillow`_ -- Python Imaging Library
* `Meshlab`_ -- programa para ver y editar mallas triangulares 3D

.. _`Pillow`: https://pillow.readthedocs.io/
.. _`MeshLab`: https://en.wikipedia.org/wiki/MeshLab
