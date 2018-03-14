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
planets, moons and so on, used in the non-profit project [A Touch of
The Universe](https://astrokit.uv.es/) on educational astronomy.

There are several programs related to images of maps and 3D files:

- mapelia - convert maps into 3D figures with reliefs.
- guapelia - optional GUI to use mapelia.
- pintelia - convert maps into colored 3D figures.
- poligoniza - form faces (polygons) from 3D points.
- stl-split - split a 3D globe into the north and south hemispheres.

The input images are jpg or png files that contain maps in any of
several possible projections (equirectangular, Mercator, central
cylindrical, Mollweide or sinusoidal).

The output of the programs are 3D files (of polygons like ply or stl,
or points in space like asc), that can be visualized and manipulated
with programs like MeshLab or Blender.

# References
