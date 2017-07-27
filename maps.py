"""
Convierte imágenes con mapas a ficheros 3D.

Toma mapas en proyección de Mercator, cónica o de Mollweide, de ficheros jpg,
png, etc., y escribe ficheros ply (polígonos) o asc (nube de puntos) con una
esfera que contiene las elevaciones deducidas del mapa en cada punto. Estos
ficheros se pueden a su vez manipular con programas como MeshLab o Blender.
"""

# Spherical coordinates convention:
#   theta: angle from the x axis to the projection of the point in the xy plane
#   phi: angle from the xy plane to the point
# so
#   x = r * cos(theta) * cos(phi)
#   y = r * sin(theta) * cos(phi)
#   z = r * sin(phi)

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
from numpy import (sin, cos, exp, arcsin, arccos, arctan, arctan2, sqrt,
                   pi, e, nan, isnan,
                   array, linspace, ones_like, zeros, average, all)


def process(args):
    if not os.path.isfile(args.image):
        sys.exit('File %s does not exist.' % args.image)

    check_caps(args.caps)

    output = args.output or '%s.%s' % (args.image.rsplit('.', 1)[0], args.type)
    if not args.overwrite:
        check_if_exists(output)

    print('Processing file %s ...' % args.image)
    img = Image.open(args.image)

    if args.fix_gaps:
        img = fill_dark(img)

    img = fix_ratios(img, args.projection)

    heights = get_heights(img, args.channel)
    if args.invert:
        heights = -heights

    projection_args = {'ptype': args.projection,
                       'npoints': args.points,
                       'scale': args.scale,
                       'caps': args.caps,
                       'meridian': not args.no_meridian,
                       'protrusion': args.protrusion}

    if args.type == 'asc':
        write_asc(output, heights, projection_args)
    elif args.type == 'ply':
        write_ply(output, heights, projection_args)

    return output


def fix_ratios(img, ptype):
    "Resize the image if ptype expects to have a different nx/ny ratio"
    nx, ny = img.size
    nys = {'mollweide': int(nx * sqrt(2) / pi),
           'equirectangular': nx // 2,
           'sinusoidal': nx // 2}
    if ptype in nys:
        ny_expected = nys[ptype]
        if abs(ny - ny_expected) > 0:
            print('You say this image is a %s projection? The ratios '
                  'do not look good (%dx%d).\nChanging them to %dx%d. '
                  'Consider fixing the original...' % (ptype, nx, ny, nx,
                                                       ny_expected))
            img = img.resize((nx, ny_expected), Image.ANTIALIAS)
    return img


def check_caps(caps):
    "Check that the caps are valid"
    # We want this so as to fail early.
    try:
        if not 0 < float(caps) < 90:
            sys.exit('caps can be an angle > 0 and < 90 (or auto or none).')
    except ValueError:
        if caps not in ['auto', 'none']:
            sys.exit('caps can be "auto", "none" or a float.')


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
    add('--projection', default='mercator',
        choices=['mercator', 'cylindrical', 'mollweide', 'equirectangular',
                 'sinusoidal'],
        help='tipo de proyección usada en el mapa')
    add('--points', type=int, default=500000,
        help='número de puntos a usar como máximo')
    add('--scale', type=float, default=0.02,
        help='fracción de radio entre el punto más bajo y más alto')
    add('--caps', default='auto',
        help='ángulo (en grados) al que llegan los casquetes (o auto o none)')
    add('--no-meridian', action='store_true', help='no añadir meridiano 0')
    add('--protrusion', type=float, default=1.2,
        help='fracción en la que sobresalen meridiano y casquetes del máximo')
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
property list uchar int vertex_index
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
        write = lambda f: fout.write(struct.pack(b'<B3i', 3, *f))
    else:
        write = lambda f: fout.write(b'3 %d %d %d\n' % f)

    for f in faces:
        write(f)


def write_asc(fname, heights, projection_args):
    "Write an asc file with the given points"
    points = project(heights, **projection_args)
    with open(fname, 'wb') as fout:
        write_vertices(fout, points, binary=False)


def project(heights, ptype, npoints, scale, caps, meridian, protrusion):
    "Return points on a sphere, modulated by the given heights"
    # The points returned look like a list of rows:
    # [[(0, x0_0, y0_0, z0_0), (1, x0_1, y0_1, z0_1), ...],
    #  [(n, x1_0, y1_0, z1_0), (n+1, x1_1, y1_1, z1_1), ...],
    #  ...]
    # This will be useful later on to connect the points and form faces.
    if not all(heights == 1):
        print('Projecting heights on a sphere...')
    ny, nx = heights.shape
    get_theta, get_phi = projection_functions(ptype, nx, ny)
    points = []
    pid = 0  # point id, used to reference the point by a number later on

    if ptype in ['mollweide', 'sinusoidal'] and caps == 'auto':
        caps = 'none'

    phi_cap = get_phi_cap(caps, get_phi(ny // 2))

    def add_cap(phi_cap, pid):
        r = 1 + protrusion * scale
        rcphin, rsphin = r * cos(phi_cap), r * sin(phi_cap)
        if phi_cap > 0:
            phi_start, phi_end, limit = pi / 2, phi_cap, r
        else:
            phi_start, phi_end, limit = phi_cap, -pi / 2, -r
        for phi in linspace(phi_start, phi_end, 10):
            row = []
            rcphi, rsphi = r * cos(phi), r * sin(phi)
            z = rsphi
            for theta in linspace(-pi, pi, max(9, int(100 * cos(phi)))):
                x = cos(theta) * rcphi
                y = sin(theta) * rcphi
                row.append((pid, x, y, z))
                pid += 1
            points.append(row)
        return pid

    # North cap.
    if caps != 'none':
        pid = add_cap(phi_cap=phi_cap, pid=pid)

    # Points from the given heights.
    hmin, hmax = heights.min(), heights.max()
    if hmax - hmin > 0.01:
        radii = 1.0 + scale * (2.0 * (heights - hmin) / (hmax - hmin) - 1.0)
    else:
        radii = ones_like(heights)
        meridian = False  # hack

    rmeridian = 1 + protrusion * scale

    n = sqrt(npoints)
    stepy = int(max(1, ny / (3 * n)))  # the 3 factor is related to 1/cos(phi)
    for j in range(0, ny, stepy):
        y_map = ny // 2 - j
        phi = get_phi(y_map)
        if isnan(phi) or abs(phi) > phi_cap:
            continue

        row = []
        cphi, sphi = cos(phi), sin(phi)
        stepx = int(max(1, nx / n) * (1 if ptype in ['mollweide', 'sinusoidal']
                                        else 1 / cphi))
        for i in range(0, nx, stepx):
            x_map = i - nx // 2
            theta = get_theta(x_map, y_map)
            if isnan(theta):
                continue

            if meridian and -0.02 < theta < 0.02:
                r = rmeridian
            else:
                r = radii[j, i]

            x = r * cos(theta) * cphi
            y = r * sin(theta) * cphi
            z = r * sphi
            row.append((pid, x, y, z))
            pid += 1
        if row:
            points.append(row)

    # South cap.
    if caps != 'none':
        pid = add_cap(phi_cap=-phi_cap, pid=pid)

    return points


def projection_functions(ptype, nx, ny):
    "Return functions to get theta, phi from x, y"
    r = nx / (2 * pi)  # reconstructing the radius from nx
    if ptype == 'mercator':
        # Mercator projection:
        #   x = r * theta
        #   y = r * log(tan(pi / 4 + phi / 2))
        # Inverse:
        #   theta = x / r
        #   phi = 2 * atan(exp(y / r)) - pi / 2
        get_theta = lambda x, y: x / r
        get_phi = lambda y: 2 * arctan(exp(y / r)) - pi / 2
    elif ptype == 'cylindrical':
        # Central cylindrical projection:
        #   x = r * theta
        #   y = r * tan(phi)
        # Inverse:
        #   theta = x / r
        #   phi = atan(y / r)
        get_theta = lambda x, y: x / r
        get_phi = lambda y: arctan2(y, r)
    elif ptype == 'mollweide':
        # Mollweide projection:
        #   x = r * 2 * sqrt(2) / pi * theta * cos(aux)
        #   y = r * sqrt(2) * sin(aux)
        # where aux is such that:  2 * aux + sin(2 * aux) = pi * sin(phi)
        # Inverse:
        #   theta = pi * x / (2 * r * sqrt(2) * cos(asin(aux)))
        #   phi = asin( ((2 * asin(aux) + sin(2 * asin(aux)) ) / pi)
        # with  aux = y / (r * sqrt(2))
        sqrt2 = sqrt(2)
        def get_theta(x, y):
            aux = y / (r * sqrt2)
            if not -1 < aux < 1:
                return nan
            aux2 = pi * x / (2 * r * sqrt2 * sqrt(1 - aux*aux))
            return aux2 if -pi < aux2 < pi else nan
        def get_phi(y):
            aux = y / (r * sqrt2)
            if not -1 < aux < 1:
                return nan
            aux2 = (2 * arcsin(aux) + sin(2 * arcsin(aux))) / pi
            return arcsin(aux2) if -1 < aux2 < 1 else nan
    elif ptype == 'equirectangular':
        # Equirectangular projection:
        #   x =  r * theta
        #   y = r * phi
        # Inverse:
        #   theta = x / r
        #   phi = y / r
        get_theta = lambda x, y: x / r
        get_phi = lambda y: y / r
    elif ptype == 'sinusoidal':
        # Sinusoidal projection:
        #   x = r * theta * cos(phi)
        #   y = r * phi
        # Inverse:
        #   theta = x / (r * cos(y / r))
        #   phi = y / r
        def get_theta(x, y):
            theta = x / (r * cos(y / r))
            return theta if -pi < theta < pi else nan
        def get_phi(y):
            return y / r
    return get_theta, get_phi


def get_phi_cap(caps, phi_auto):
    "Return the angle at which the cap ends"
    if caps == 'auto':
        return phi_auto
    elif caps == 'none':
        return pi / 2
    else:  # caps is an angle then
        return pi / 2 - pi * float(caps) / 180


def get_faces(points):
    "Yield faces as triplets of point indices"
    # points must be a list of rows, each containing the actual points
    # that correspond to a (closed!) section of an object.
    print('Forming the faces...')

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
