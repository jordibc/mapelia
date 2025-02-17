#!/usr/bin/env python3

"""
Paint with colors over the surface of a sphere an image with a map.

It takes maps from jpg files, png, and so on, and writes ply (polygon) files.
"""

# Spherical coordinates convention:
#   theta: angle from the x axis to the projection of the point in the xy plane
#   phi: angle from the xy plane to the point
# That is, theta is the longitude and phi is the latitude:
#   x = r * cos(theta) * cos(phi)
#   y = r * sin(theta) * cos(phi)
#   z = r * sin(phi)

import sys
import os
import struct
from collections import namedtuple

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt
from PIL import Image
from numpy import sin, cos, sqrt, isnan, array

import maps
try:
    import projections
    assert projections.__version__ == '1.3.0'
except (ImportError, AssertionError, AttributeError) as e:
    sys.exit('projections module not ready. You may want to first run:\n'
             '  %s setup.py develop' % sys.executable)

Point = namedtuple('Point', ['pid', 'x', 'y', 'z', 'r', 'g', 'b', 'a'])


def main():
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut
    add('image', help='image file with the map')
    add('-o', '--output', default='',
        help='output file (if empty, it is generated from the image file name)')
    add('--overwrite', action='store_true',
        help='do not check if the output file already exists')
    add('--projection', default='mercator',
        choices=['mercator', 'cylindrical', 'mollweide', 'equirectangular',
                 'sinusoidal'],
        help='projection used in the map')
    add('--points', type=int, default=0,
        help='maximum number of points to use (or 0 to use all in the image)')
    add('--no-ratio-check', action='store_true',
        help='do not fix the height/width ratio for certain projections')
    add('--fix-gaps', action='store_true',
        help='try to fill the gaps in the map')
    args = parser.parse_args()
    output = process(args)
    print('The output is in file %s' % output)


def process(args):
    if not os.path.isfile(args.image):
        sys.exit('File %s does not exist.' % args.image)

    output = args.output or '%s.ply' % args.image.rsplit('.', 1)[0]
    if not args.overwrite:
        maps.check_if_exists(output)

    print(maps.green('Processing file %s ...' % args.image))
    img = Image.open(args.image)

    if args.fix_gaps:
        img = maps.fill_dark(img)

    if not args.no_ratio_check:
        img = maps.fix_ratios(img, args.projection)

    projection_args = {'ptype': args.projection,
                       'npoints': args.points}

    imx = array(img.convert('RGBA'))

    write_ply(output, imx, projection_args)

    return output


def write_ply(fname, img, projection_args):
    "Write a ply file with the given points and deduced faces"
    points = project(img, **projection_args)
    faces = projections.get_faces(points)

    with open(fname, 'wb') as fout:
        fout.write(ply_header(nvertices=points[-1][-1][0]+1, nfaces=len(faces)))
        write_vertices(fout, points)
        write_faces(fout, faces)


def ply_header(nvertices, nfaces):
    "Return header of a ply file with the given number of vertices and faces"
    return b"""\
ply
format binary_little_endian 1.0
element vertex %d
property float x
property float y
property float z
property uchar red
property uchar green
property uchar blue
property uchar alpha
element face %d
property list uchar int vertex_index
end_header
""" % (nvertices, nfaces)


def write_vertices(fout, points):
    "Write in fout the tuples and colors that define the vertices"
    for row in points:
        for p, x, y, z, r, g, b, a in row:
            fout.write(struct.pack(b'<3f4B', x, y, z, r, g, b, a))


def write_faces(fout, faces):
    "Write in fout the lists of indices that define the faces"
    for f in faces:
        fout.write(struct.pack(b'<B3i', 3, *f))


def project(imx, ptype, npoints):
    "Return points on a sphere"
    # The points returned look like a list of rows:
    # [[(0, x0_0, y0_0, z0_0, r0_0, g0_0, b0_0),
    #   (1, x0_1, y0_1, z0_1, r0_1, g0_1, b0_1), ...],
    #  [(n, x1_0, y1_0, z1_0, ...), (n+1, x1_1, y1_1, z1_1, ...), ...],
    #  ...]
    # This will be useful later on to connect the points and form faces.
    ny, nx, _ = imx.shape
    get_theta, get_phi = projections.projection_functions(ptype, nx, ny)
    points = []
    pid = 0  # point id, used to reference the point by a number later on

    n = sqrt(npoints)
    stepy = int(max(1, ny / (3 * n))) if n > 0 else 1
    # the 3 factor is related to 1/cos(phi)

    r = 1
    for j in range(0, ny, stepy):
        y_map = ny // 2 - j
        phi = get_phi(y_map)
        if isnan(phi):
            continue

        row = []
        cphi, sphi = cos(phi), sin(phi)
        stepx = int(max(1, nx / n) * (1 if ptype in ['mollweide', 'sinusoidal']
                                        else 1 / cphi)) if n > 0 else 1
        for i in range(0, nx, stepx):
            x_map = i - nx // 2
            theta = get_theta(x_map, y_map)
            if isnan(theta):
                continue

            x = r * cos(theta) * cphi
            y = r * sin(theta) * cphi
            z = r * sphi
            row.append(Point(pid, x, y, z, *imx[j, i]))
            pid += 1
        if row:
            points.append(row)

    return points



if __name__ == '__main__':
    main()
