"""
Convierte imágenes con mapas a ficheros 3D.

Toma mapas en proyección de Mercator, cónica o de Mollweide, de ficheros jpg,
png, etc., y escribe ficheros ply (polígonos) o asc (nube de puntos) con una
esfera que contiene las elevaciones deducidas del mapa en cada punto. Estos
ficheros se pueden a su vez manipular con programas como MeshLab o Blender.
"""

# TODO:
# * Allow the use of an external 1xN image with the colors that
#   correspond to different heights.
# * Clean up the project() and get_faces() functions.
# * Remove the hack of  faces = list(get_faces(points_sphere))  in write_ply()

import sys
import os
import struct

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt
from PIL import Image
from numpy import (sin, cos, exp, arcsin, arctan, sqrt, pi, e,
                   array, linspace, ones_like, zeros, average)


def process(args):
    output = args.output or '%s.%s' % (args.image.rsplit('.', 1)[0], args.type)
    if not args.overwrite:
        check_if_exists(output)

    print('Processing file %s ...' % args.image)
    img = Image.open(args.image)

    if args.fix_gaps:
        img = fill_dark(img)

    heights = get_heights(img, args.channel)
    if args.invert:
        heights = -heights

    projection_args = {'ptype': args.projection,
                       'npoints': args.points,
                       'scale': args.scale,
                       'poles': not args.no_poles,
                       'meridian': not args.no_meridian}

    if args.type == 'asc':
        write_asc(output, heights, projection_args)
    elif args.type == 'ply':
        write_ply(output, heights, projection_args)

    return output


def check_if_exists(fname):
    if os.path.exists(fname):
        answer = input('File %s already exists. Overwrite? [y/n] ' % fname)
        if not answer.lower().startswith('y'):
            sys.exit('Cancelling.')


def get_parser():
    "Return the parser object with all the arguments"
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut
    add('image', help='fichero de imagen con el mapa')
    add('-o', '--output', default='',
        help='fichero de salida (si vacío, se genera a partir del de entrada)')
    add('--overwrite', action='store_true',
        help='no comprobar si el fichero de salida existe')
    add('--type', choices=['ply', 'asc'], default='ply',
        help='tipo de fichero a generar')
    add('--channel', default='val',
        choices=['r', 'g', 'b', 'average', 'hue', 'sat', 'val', 'color'],
        help='canal que contiene la información de la elevación')
    add('--invert', action='store_true', help='invierte las elevaciones')
    add('--projection', choices=['mercator', 'cylindrical', 'mollweide'],
        default='mercator', help='tipo de proyección usada en el mapa')
    add('--points', type=int, default=500000,
        help='número de puntos a usar como máximo')
    add('--scale', type=float, default=0.02,
        help='fracción de radio entre el punto más bajo y más alto')
    add('--no-poles', action='store_true', help='no añadir polos')
    add('--no-meridian', action='store_true', help='no añadir meridiano 0')
    add('--fix-gaps', action='store_true',
        help='intenta rellenar los huecos en el mapa')
    return parser


def write_ply(fname, heights, projection_args):
    "Write a ply file with the given points and deduced faces"
    points = project(heights, **projection_args)

    points_sphere = project(ones_like(heights), **projection_args)
    faces = list(get_faces(points_sphere))
    # we use the points of a sphere without distortions for the
    # connection of the points forming the faces

    with open(fname, 'wb') as fout:
        fout.write(ply_header(nvertices=points[-1][-1][0]+1, nfaces=len(faces)))
        write_vertices(fout, points)
        write_faces(fout, faces)


def ply_header(nvertices, nfaces):
    "Return header of a ply file with the given number of vertices and faces"
    return b"""\
ply
format binary_little_endian 1.0
comment made by mapelia
element vertex %d
property float x
property float y
property float z
element face %d
property list int int vertex_index
end_header
""" % (nvertices, nfaces)


def write_vertices(fout, points, binary=True):
    "Write in fout the tuples of x, y, z that define the vertices"
    if binary:
        write = lambda x, y, z: fout.write(struct.pack(b'<3f', x, y, z))
    else:
        write = lambda x, y, z: fout.write(b'%g %g %g\n' % (x, y, z))

    for row in points:
        for p, x, y, z in row:
            write(x, y, z)


def write_faces(fout, faces, binary=True):
    "Write in fout the lists of indices that define the faces"
    if binary:
        write = lambda f: fout.write(struct.pack(b'<i3i', 3, *f))
    else:
        write = lambda f: fout.write(b'3 %d %d %d\n' % f)
    for f in faces:
        write(f)


def write_asc(fname, heights, projection_args):
    "Write an asc file with the given points"
    points = project(heights, **projection_args)
    with open(fname, 'wb') as fout:
        write_vertices(fout, points, binary=False)


# Mercator projection:
#   x = r * theta
#   y = r * log(tan(pi / 4 + phi / 2))
# Inverse:
#   theta = x / r
#   phi = 2 * atan(exp(y / r)) - pi / 2
# with r = nx / (2 * pi)
#
# Central cylindrical projection:
#   x = r * theta
#   y = r * tan(phi)
# Inverse:
#   theta = x / r
#   phi = atan(y / r)
# with r = nx / (2 * pi)
#
# Mollweide projection:
#   x = r * 2 * sqrt(2) / pi * theta * cos(aux)
#   y = r * sqrt(2) * sin(aux)
# where aux is such that:  2 * aux + sin(2 * aux) = pi * sin(phi)
# Inverse:
#   theta = pi * x / (2 * r * sqrt(2) * cos(aux))
#   phi = asin(((2 * aux) + sin(2 * aux)) / pi)
# with  aux = asin(y / (r * sqrt(2))  and  r = nx / (2 * pi)
def project(heights, ptype, npoints, scale, poles, meridian):
    "Return points on a sphere, modulated by the given heights"
    # The points returned look like a list of rows:
    # [[(0, x0_0, y0_0, z0_0), (1, x0_1, y0_1, z0_1), ...],
    #  [(n, x1_0, y1_0, z1_0), (n+1, x1_1, y1_1, z1_1), ...],
    #  ...]
    # This will be useful later on to connect the points and form faces.
    ny, nx = heights.shape

    # Function to go from the y to the phi angle.
    if ptype == 'mercator':
        get_theta = lambda x, y: pi * (2 * i / nx - 1)
        get_phi = lambda x, y: 2 * arctan(exp(pi * y / nx)) - pi / 2
    elif ptype == 'cylindrical':
        get_theta = lambda x, y: pi * (2 * i / nx - 1)
        get_phi = lambda x, y: arctan(2 * pi * y / nx)
    elif ptype == 'mollweide':
        sqrt2 = sqrt(2)
        def get_theta(x, y):
            aux = arcsin(2 * pi * y / (nx * sqrt2))
            return pi * pi * x / (nx * sqrt2 * cos(aux))
        def get_phi(x, y):
            aux = arcsin(2 * pi * y / (nx * sqrt2))
            return arcsin(((2 * aux) + sin(2 * aux)) / pi)
        raise NotImplementedError

    points = []
    pid = 0

    def add_pole(phi_n, pid):
        r = 1 + 1.2 * scale
        rcphin, rsphin = r * cos(phi_n), r * sin(phi_n)
        if phi_n > 0:
            phi_start, phi_end, limit = pi / 2, phi_n, r
        else:
            phi_start, phi_end, limit = phi_n, -pi / 2, -r
        for phi in linspace(phi_start, phi_end, 10):
            row = []
            rcphi, rsphi = r * cos(phi), r * sin(phi)
            z = rsphin + (limit - rsphin) * exp(- rcphi**2 / rcphin**2)
            for theta in linspace(-pi, pi, max(5, int(100 * cos(phi)))):
                x = cos(theta) * rcphi
                y = sin(theta) * rcphi
                row.append((pid, x, y, z))
                pid += 1
            points.append(row)
        return pid

    # North pole.
    if poles and ptype != 'mollweide':
        pid = add_pole(phi_n=get_phi(0, ny), pid=pid)

    # Points from the given heights.
    hmin, hmax = heights.min(), heights.max()
    if hmax - hmin > 0.01:
        radii = 1 + scale * (2 * (heights - hmin) / (hmax - hmin) - 1)
    else:
        radii = ones_like(heights)
        meridian = False  # hack

    n = sqrt(npoints)
    stepx = int(max(1, nx / n))  # will be multiplied by 1/cos(phi)
    stepy = int(max(1, ny / (3 * n)))  # the 3 factor is related to 1/cos(phi)

    rmeridian = (1 + 1.2 * scale) * (1 / (e * sin(get_phi(0, ny))) + 1 - 1 / e)
    # this way it connects nicely with the poles

    for j in range(0, ny, stepy):
        y_map = ny - 2 * j
        phi = get_phi(0, y_map)

        row = []
        cphi, sphi = cos(phi), sin(phi)
        for i in range(0, nx, stepx * int(1 / cphi)):
            x_map = i
            theta = get_theta(x_map, y_map)

            if meridian and -0.02 < theta < 0.02:
                r = rmeridian
            else:
                r = radii[j, i]

            x = r * cos(theta) * cphi
            y = r * sin(theta) * cphi
            z = r * sphi
            row.append((pid, x, y, z))
            pid += 1
        points.append(row)

    # South pole.
    if poles and ptype != 'mollweide':
        pid = add_pole(phi_n=get_phi(0, -ny), pid=pid)

    return points


def get_faces(points):
    "Yield faces as triplets of point indices"
    # points must be a list of rows, each containing the actual points
    # that correspond to a (closed!) section of an object.

    # This follows the "walking the dog" algorithm that I just made up.
    # It seems to work fine when using the points of a sphere...

    def dist2(p0, p1):  # geometric distance (squared) between two points
        _, x0, y0, z0 = p0
        _, x1, y1, z1 = p1
        return (x1 - x0)**2 + (y1 - y0)**2 + (z1 - z0)**2

    # dog            <-- previous row
    #  ^
    #  i  ->  i+1    <-- current row
    # The position i (where the human is) is updated, and then the dog is
    # moved (in the previous row) until it cannot be closer to the human,
    # making triangles along the way. Then, a new triangle is made from the
    # current position to the next one and the dog (i -> i+1 -> dog).
    for j in range(1, len(points)):
        row_previous = points[j - 1]
        row_current = points[j]
        dog = 0
        h = lambda: row_current[i]              # point where the human is
        d = lambda: row_previous[dog]           # point where the dog is
        dw = lambda: row_previous[dog_walking]  # point where the dog goes
        for i in range(len(row_current)):
            dog_walking = dog
            dist = dist2(h(), d())
            while True:  # let the dog walk until it's as close as possible
                dog_walking = (dog_walking + 1) % len(row_previous)
                dist_new = dist2(h(), dw())
                if dist_new < dist:
                    yield (h()[0], dw()[0], d()[0])
                    dog = dog_walking
                    dist = dist_new
                else:
                    break
            yield (h()[0], row_current[(i + 1) % len(row_current)][0], d()[0])
        while dog != 0:  # we have to close the figure
            dog_walking = (dog + 1) % len(row_previous)
            yield (row_current[0][0], dw()[0], d()[0])
            dog = dog_walking


def fill_dark(img, too_dark_value=30, darkest_fill=50):
    "Fill dark values in the image (which correspond to areas with no data)"
    print('Filling dark areas with nearby color...')
    img_filled = img.convert('HSV')
    last_fill = (255, 255, 255)
    nx, ny = img_filled.size
    for j in range(ny):
        for i in range(nx):
            hsv = img_filled.getpixel((i, j))
            if hsv[2] < too_dark_value:
                img_filled.putpixel((i, j), last_fill)
            elif hsv[2] > darkest_fill:
                last_fill = hsv
    return img_filled.convert('RGBA')


def get_heights(img, channel='value'):
    "Return an array with the heights extracted from the image"
    print('Extracting heights from the image...')
    if channel in ['r', 'g', 'b', 'average']:
        # These channels are straigthforward: higher values are higher heights.
        imx = array(img.convert('RGBA'))
        if   channel == 'r':  return imx[:,:,0]
        elif channel == 'g':  return imx[:,:,1]
        elif channel == 'b':  return imx[:,:,2]
        elif channel == 'average':
            return average(imx, axis=2)
    elif channel in ['hue', 'sat', 'val']:
        # These channels are straigthforward: higher values are higher heights.
        imxHSV = array(img.convert('RGBA').convert('HSV'))
        if   channel == 'hue':  return imxHSV[:,:,0]
        elif channel == 'sat':  return imxHSV[:,:,1]
        elif channel == 'val':  return imxHSV[:,:,2]
    elif channel == 'color':
        # This channel is *not* straigthforward.
        rgb2height = find_rgb2height(img)
        nx, ny = img.size
        heights = zeros((ny, nx))
        for j in range(ny):
            for i in range(nx):
                heights[j, i] = rgb2height[img.getpixel((i, j))]
        return heights


def find_rgb2height(img):
    "Return a dict to transform rgb tuples to heights"
    # It is assumed that low heights correspond to big hues, and for
    # the same hue a lower color value corresponds to higher heights.
    imgHSV = img.convert('RGBA').convert('HSV')
    nx, ny = img.size
    rgb2hv = {}
    for i in range(nx):
        for j in range(ny):
            h, s, v = imgHSV.getpixel((i, j))
            rgb2hv[img.getpixel((i, j))] = (-h, v)
    hv2height = {hv: i for i, hv in enumerate(sorted(rgb2hv.values()))}
    rgb2height = {}
    for rgb in rgb2hv:
        if rgb not in rgb2height:
            rgb2height[rgb] = hv2height[rgb2hv[rgb]]
    return rgb2height
