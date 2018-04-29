---
title: 'Mapelia and friends: create 3D models from maps'
tags:
- 3d
- maps
- astronomy
- outreach
- python
- stl
authors:
- name: Amelia Ortiz-Gil
  orcid: 0000-0003-1485-0252
  affiliation: 1
- name: Jordi Burguet-Castell
  orcid: 0000-0002-9198-5380
  affiliation: 2
affiliations:
- name: University of Valencia, Valencia, Spain
  index: 1
- name: None
  index: 2
date: 13 March 2018
bibliography: paper.bib
---

# Summary

This software was created to help with the development of 3D models of
planets, moons and so on, used in the non-profit project *A Touch of
The Universe* [@astrokit] on educational astronomy.

There are several programs related to images of maps and 3D files:

- `mapelia` - convert maps into 3D figures with reliefs.
- `guapelia` - optional GUI to use mapelia.
- `pintelia` - convert maps into colored 3D figures.
- `poligoniza` - form faces (polygons) from 3D points.
- `stl-split` - split a 3D globe into the north and south hemispheres.

The input images are `jpg` or `png` files that contain maps (that is,
gridded datasets where the value of each pixel is the elevation) in
any of several possible projections (equirectangular, Mercator,
central cylindrical, Mollweide or sinusoidal).

The output of the programs are 3D files (of polygons like `ply` or
`stl`, or points in space like `asc`), that can be visualized and
manipulated with programs like MeshLab or Blender.

In the project *A Touch of The Universe*, the generated `stl` files
are directly printed with a 3D printer, to create a physical
representation of diverse planets and moons. Those printed models are
then used to do outreach in astronomy at the *Aula del Cel (The Sky
Classroom)* [@aula_del_cel] in the Astronomical Observatory of the
University of Valencia among other places.

# References

Maps
----

* [Finding and Using Space Image Data](http://www.planetary.org/explore/space-topics/space-imaging/data.html)
* [Planetary Data System](https://en.wikipedia.org/wiki/Planetary_Data_System)

Projections
-----------

* [equirectangular](https://en.wikipedia.org/wiki/Equirectangular_projection)
* [Mercator](https://en.wikipedia.org/wiki/Mercator_projection)
* [central cylindrical](https://en.wikipedia.org/wiki/Central_cylindrical_projection)
* [Mollweide](https://en.wikipedia.org/wiki/Mollweide_projection)
* [sinusoidal](https://en.wikipedia.org/wiki/Sinusoidal_projection)

Formats
-------

* [ply](https://en.wikipedia.org/wiki/PLY_(file_format))
* [stl](https://en.wikipedia.org/wiki/STL_(file_format))
* [asc](https://codeyarns.com/2011/08/17/asc-file-format-for-3d-points/)

Processing
----------

* [Pillow](https://pillow.readthedocs.io/)
* [NumPy](http://www.numpy.org/)
* [Meshlab](https://en.wikipedia.org/wiki/MeshLab)
* [Blender](https://www.blender.org/)
