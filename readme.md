# mapelia and friends

This software was created to help with the development of 3D models of
planets, moons and so on, used in the non-profit project [A Touch of
The Universe](https://astrokit.uv.es/) on educational astronomy.

There are several programs related to images of maps and 3D files:

- `mapelia` - convert maps into 3D figures with reliefs.
- `guapelia` - optional GUI to use mapelia.
- `pintelia` - convert maps into colored 3D figures.
- `poligoniza` - form faces (polygons) from 3D points.
- `stl-split` - split a 3D globe into the north and south hemispheres.
- `smooth` - create a smoothed version of an image.

The images are `jpg` or `png` files that contain maps (that is,
gridded datasets where the value of each pixel is the elevation) in
any of the following projections:
[equirectangular](https://en.wikipedia.org/wiki/Equirectangular_projection),
[Mercator](https://en.wikipedia.org/wiki/Mercator_projection),
[central
cylindrical](https://en.wikipedia.org/wiki/Central_cylindrical_projection),
[Mollweide](https://en.wikipedia.org/wiki/Mollweide_projection) or
[sinusoidal](https://en.wikipedia.org/wiki/Sinusoidal_projection).

The output of the programs are 3D files (of polygons like
[ply](https://en.wikipedia.org/wiki/PLY_(file_format)) or
[stl](https://en.wikipedia.org/wiki/STL_(file_format)), or points in
space like
[asc](https://codeyarns.com/2011/08/17/asc-file-format-for-3d-points/)),
that can be visualized and manipulated with programs like
[MeshLab](https://en.wikipedia.org/wiki/MeshLab) or
[Blender](https://www.blender.org/).

In the project *A Touch of The Universe*, the generated `stl` files
are directly printed with a 3D printer, to create a physical
representation of diverse planets and moons. Those printed models are
then used to do outreach in astronomy at the [Aula del Cel (The Sky
Classroom)](https://aorgil.blogs.uv.es/aula-del-cel/) in the
Astronomical Observatory of the University of Valencia among other
places.


## Installing

### Quick installation

Just download this repository, go to its folder and run:

```sh
$ pip install -e .
```

Or, if you already have installed the prerequisites (mainly `numpy`
and `pillow`, see below), then you can directly run the programs.


### Faster execution with Cython

The main computation is done with `projections.py`, but we can create
a faster compiled module. To do it, you can add the optional `cython`
dependency:

```sh
$ pip install -e '.[cython]'
```

Then, you can run:

```sh
$ python setup.py develop
```

If you don't do it, `mapelia` will still work, but just using the
slower version.


### Prerequisites

All the programs need [Python 3](https://www.python.org/downloads/) to
run. In addition, most need the following packages:
[Pillow](https://pillow.readthedocs.io/) and
[NumPy](https://www.numpy.org/).

On a recent Debian system, you can install them with:

```sh
$ sudo apt install python3 python3-pil python3-numpy
```

This will allow you to run `mapelia`, `pintelia`, `poligoniza`,
`stl-split` and `smooth`.

If you haven't installed them with `pip install -e .` you can still
run them like `./mapelia/mapelia.py` and so on.


### Optional GUI

In case you want to use the optional Graphical User Interface
`guapelia` you will also need [GTK+
3](https://python-gtk-3-tutorial.readthedocs.io/).

```sh
$ sudo apt install python3-gi libgtk-3-0
```


## Tests

You can run some tests that use maps from the `examples` directory
with:

```sh
$ ./tests.py
```


## References

### Maps

- [Space Image Library](https://www.planetary.org/space-images)
- [Planetary Data System](https://en.wikipedia.org/wiki/Planetary_Data_System)


### Projections

- [Equirectangular](https://en.wikipedia.org/wiki/Equirectangular_projection)
- [Mercator](https://en.wikipedia.org/wiki/Mercator_projection)
- [Central cylindrical](https://en.wikipedia.org/wiki/Central_cylindrical_projection)
- [Mollweide](https://en.wikipedia.org/wiki/Mollweide_projection)
- [Sinusoidal](https://en.wikipedia.org/wiki/Sinusoidal_projection)


### Formats

- [ply](https://en.wikipedia.org/wiki/PLY_(file_format)) - "polygons"
  in 3D, also admits colors
- [stl](https://en.wikipedia.org/wiki/STL_(file_format)) -
  "stereolitography", triangles in 3D, not as nice as `ply` but much
  used for 3D printing
- [asc](https://codeyarns.com/2011/08/17/asc-file-format-for-3d-points/) -
  only 3D points


### Processing

- [Pillow](https://pillow.readthedocs.io/) - Python Imaging Library
- [NumPy](https://www.numpy.org/) - library with support for multi-dimensional arrays
- [MeshLab](https://en.wikipedia.org/wiki/MeshLab) - program to view and edit 3D meshes
- [Blender](https://www.blender.org/) - 3D computer graphics toolset


---

# Descriptions, examples and usage of the programs

## mapelia

`mapelia` is a program to manipulate files with map images and
transform them into 3D figures with their heights extracted from the
map.

### Example

Starting with the following image:

![](examples/venus.png)

we run:

```sh
$ mapelia examples/venus.png
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
```

and get:

![](examples/screenshot_meshlab.png)

### Usage

```
usage: mapelia [-h] [--output OUTPUT] [--overwrite] [--type {ply,asc,stl}]
               [--channel {r,g,b,average,hue,sat,val,color}] [--invert]
               [--projection {mercator,central-cylindrical,mollweide,equirectangular,sinusoidal,half-sphere}]
               [--points POINTS] [--scale SCALE] [--caps CAPS]
               [--caps-height CAPS_HEIGHT] [--logo-north LOGO_NORTH]
               [--logo-north-scale LOGO_NORTH_SCALE] [--logo-south LOGO_SOUTH]
               [--logo-south-scale LOGO_SOUTH_SCALE]
               [--meridians-pos [POSITION [POSITION ...]]]
               [--meridians-widths [WIDTH [WIDTH ...]]]
               [--meridians-height MERIDIANS_HEIGHT]
               [--equator-width EQUATOR_WIDTH]
               [--equator-height EQUATOR_HEIGHT] [--thickness THICKNESS]
               [--no-ratio-check] [--no-faces] [--no-close-figure]
               [--blur BLUR] [--fix-gaps] [--config CONFIG]
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
  --projection mercator_central-cylindrical_mollweide_equirectangular_sinusoidal_half-sphere
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
  --no-faces            add no faces, only points (default: False)
  --no-close-figure     do not stitch borders (default: False)
  --blur BLUR           amount of pixels used to smooth the image (default: 0)
  --fix-gaps            try to fill the gaps in the map (default: False)
  --config CONFIG       file with default parameters (default: )
```


## pintelia

`pintelia` is a program to project maps into 3D spheres with the
original colors of the map.


### Example

By running:

```sh
$ pintelia examples/earth_equirectangular.jpg --proj equirectangular
Processing file examples/earth_equirectangular.jpg ...
- Forming faces...
The output is in file examples/earth_equirectangular.ply
```

we get:

![](examples/screenshot_meshlab_pintelia.png)


### Usage

```
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
```


## poligoniza

`poligoniza` takes files of 3D points (`.asc`) and tries to join them
forming the faces of a solid.

The points in the original file must be in a certain order so that the
faces are correctly formed. For example, the order in which `mapelia`
generates the points (when it does not project logos too).


### Example

```sh
$ poligoniza venus.asc --type stl --invert
Processing file venus.asc ...
- Forming faces...
The output is in file venus.stl
```


### Usage

```
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
```


## stl-split

Split an stl into its north and south hemispheres. Optionally, split
it into two files with all the points before and after a given one.


### Example

```sh
$ stl-split mars.stl
Processing file mars.stl ...
Writing file mars_N.stl ...
Writing file mars_S.stl ...
```


### Usage

```
usage: stl-split [-h] [-n NAME] [--zcut ZCUT] [--discard-border]
                 [--number NUMBER] [--overwrite] [--ignore-check]
                 file

Split an stl file. The idea is to help post-processing stl files made with
mapelia, so they can be printed more easily. It does not modify the original
file, but creates two new files that end with "_N.stl" and "_S.stl" (or
"_head.stl" and "_tail.stl" if using the option --number).

positional arguments:
  file                  stl file

optional arguments:
  -h, --help            show this help message and exit
  -n NAME, --name NAME  output file (if empty, it is generated from the image
                        file name) (default: )
  --zcut ZCUT           z value of the cutting xy-plane (or auto) (default: 0)
  --discard-border      put triangles not cleanly cut in a "_discarded.stl"
                        file (default: False)
  --number NUMBER       split by leaving a given number of triangles in the
                        first file (default: 0)
  --overwrite           do not check if the output files already exist
                        (default: False)
  --ignore-check        go ahead even if the input file does not look like an
                        stl (default: False)
```


## smooth

Create a smoothed version of an image.


### Example

```sh
$ smooth starmap.jpg
Writing file starmap_smoothed.jpg ...
```


### Usage

```
usage: smooth [-h] [--output OUTPUT] [--overwrite] [--invert]
              [--intensity INTENSITY]
              image

Create a smoothed version of an image.

positional arguments:
  image                 image file with the map

optional arguments:
  -h, --help            show this help message and exit
  --output OUTPUT       output file (if empty, it is generated from the image
                        file name) (default: )
  --overwrite           do not check if the output file already exists
                        (default: False)
  --invert              invert the colors of the image (default: False)
  --intensity INTENSITY
                        intensity of the smoothing (default: 10)
```
