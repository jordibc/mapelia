mapelia and friends
===================

This repository contains several programs related to images of maps
and 3D files.

* ``mapelia`` - convert maps into 3D figures with reliefs.
* ``guapelia`` - optional GUI to use mapelia.
* ``pintelia`` - convert maps into colored 3D figures.
* ``poligoniza`` - form faces (polygons) from 3D points.
* ``stl-split`` - split a 3D globe into the north and south hemispheres.

The images are ``jpg`` or ``png`` files that contain maps in any of
the following projections: `equirectangular`_, `Mercator`_, `central
cylindrical`_, `Mollweide`_ or `sinusoidal`_.

.. _`equirectangular`: https://en.wikipedia.org/wiki/Equirectangular_projection
.. _`Mercator`: https://en.wikipedia.org/wiki/Mercator_projection
.. _`central cylindrical`: https://en.wikipedia.org/wiki/Central_cylindrical_projection
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

so as to generate the ``projections`` module from
``projections.c``. Don't worry about forgetting this: trying to run
directly ``mapelia`` will warn you about the need to do it.

If you also want to modify the file ``projections.pyx``, you'll first
need to run::

  $ cython3 -a projections.pyx

to regenerate the file ``projections.c``.


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
                 [--meridians-height MERIDIANS_HEIGHT]
                 [--equator-width EQUATOR_WIDTH]
                 [--equator-height EQUATOR_HEIGHT] [--thickness THICKNESS]
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
    --equator-width EQUATOR_WIDTH
                          width (in degrees) of the equator (0 for no equator)
                          (default: 0)
    --equator-height EQUATOR_HEIGHT
                          elevation of the equator (default: 1.02)
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

``pintelia`` is a program to project maps into 3D spheres with the original colors
of the map.

Example
-------

By running::

  $ ./pintelia examples/earth_equirectangular.jpg --proj equirectangular
  Processing file examples/earth_equirectangular.jpg ...
  - Forming faces...
  The output is in file examples/earth_equirectangular.ply

we get:

.. image:: examples/screenshot_meshlab_pintelia.png


Usage
-----

  usage: pintelia [-h] [-o OUTPUT] [--overwrite]
                  [--projection {mercator,cylindrical,mollweide,equirectangular,sinusoidal}]
                  [--points POINTS] [--no-ratio-check] [--fix-gaps]
                  image

  Paint with colors over the surface of a sphere an image with a map. It takes
  maps from jpg files, png, and so on, and writes ply (polygon) files.

  positional arguments:
    image                 image file with the map

  optional arguments:
    -h, --help            show this help message and exit
    -o OUTPUT, --output OUTPUT
                          output file (if empty, it is generated from the image
                          file name) (default: )
    --overwrite           do not check if the output file already exists
                          (default: False)
    --projection mercator_central-cylindrical_mollweide_equirectangular_sinusoidal
                          projection used in the map (default: mercator)
    --points POINTS       maximum number of points to use (or 0 to use all in
                          the image) (default: 0)
    --no-ratio-check      do not fix the height/width ratio for certain
                          projections (default: False)
    --fix-gaps            try to fill the gaps in the map (default: False)


poligoniza
==========

``poligoniza`` takes files of 3D points (``.asc``) and tries to join them
forming the faces of a solid.

The points in the original file must be in a certain order so that the faces
are correctly formed. For example, the order in which ``mapelia`` generates
the points (when it does not project logos too).

Example
-------

::

  $ ./poligoniza venus.asc --type stl --invert
  Processing file venus.asc ...
  - Forming faces...
  The output is in file venus.stl

Usage
-----

  usage: poligoniza [-h] [-o OUTPUT] [--overwrite] [--type {ply,stl}] [--ascii]
                    [--invert] [--row-length ROW_LENGTH]
                    file

  Create a file of polygons (.ply or .stl) from one with only the 3D points
  (.asc). The original asc file must have the points in the order that
  corresponds to the sections of a quasi-spherical object.

  positional arguments:
    file                  asc file with the points coordinates

  optional arguments:
    -h, --help            show this help message and exit
    -o OUTPUT, --output OUTPUT
                          output file (if empty, it is generated from the image
                          file name) (default: )
    --overwrite           do not check if the output file already exists
                          (default: False)
    --type ply_stl        type of 3D file to generate (default: ply)
    --ascii               write the resulting ply file in ascii (default: False)
    --invert              invert the orientations of the faces (default: False)
    --row-length ROW_LENGTH
                          maximum number of points to use (or 0 to autodetect)


stl-split
=========

Split an stl into its north and south sides.

Example
-------

::

  $ ./stl-split mars.stl
  Processing file mars.stl ...
  Writing file mars_N.stl ...
  Writing file mars_S.stl ...

Usage
-----

  usage: stl-split [-h] [-n NAME] [--number NUMBER] [--overwrite]
                   [--ignore-check]
                   file

  Split an stl file. The idea is to help post-procssing stl files made with
  mapelia, so they can be printed more easily. It does not modify the original
  file, but creates two new files that end with "_N.stl" and "_S.stl" (or
  "_head.stl" and "_tail.stl" if using the option --number).

  positional arguments:
    file                  stl file

  optional arguments:
    -h, --help            show this help message and exit
    -n NAME, --name NAME  output file (if empty, it is generated from the image
                          file name) (default: )
    --number NUMBER       split by leaving a given number of triangles in the
                          first file (default: 0)
    --overwrite           do not check if the output files already exist
                          (default: False)
    --ignore-check        go ahead even if the input file does not look like an
                          stl (default: False)


References
==========

Maps
----

* `Finding and Using Space Image Data`_
* `Planetary Data System`_

.. _`Finding and Using Space Image Data`: http://www.planetary.org/explore/space-topics/space-imaging/data.html
.. _`Planetary Data System`: https://en.wikipedia.org/wiki/Planetary_Data_System

Projections
-----------

* `equirectangular`_
* `Mercator`_
* `central cylindrical`_
* `Mollweide`_
* `sinusoidal`_

Formats
-------

* `ply`_ - "polygons" in 3D, also admits colors.
* `stl`_ - "stereolitography", triangles in 3D, not as nice as ``ply`` but much used for 3D printing.
* `asc`_ - only 3D points.


Processing
----------

* `Pillow`_ - Python Imaging Library.
* `Meshlab`_ - program to view and edit 3D meshes.

.. _`Pillow`: https://pillow.readthedocs.io/
