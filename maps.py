"""
Convierte imágenes con mapas a ficheros 3D.

Toma mapas de ficheros jpg, png, etc., y escribe ficheros ply (polígonos) o asc
(nube de puntos) con una esfera que contiene las elevaciones deducidas del mapa
en cada punto. Estos ficheros se pueden a su vez manipular con programas como
MeshLab o Blender.
"""

# Spherical coordinates convention:
#   theta: angle from the x axis to the projection of the point in the xy plane
#   phi: angle from the xy plane to the point
# That is, theta is the longitude and phi is the latitude:
#   x = r * cos(theta) * cos(phi)
#   y = r * sin(theta) * cos(phi)
#   z = r * sin(phi)

# TODO:
# * Allow the use of an external 1xN image with the colors that
#   correspond to different heights.
# * Add option to low-pass filter the image. See:
#   https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.convolve2d.html
#   https://tomroelandts.com/articles/how-to-create-a-simple-low-pass-filter

import sys
import os
import struct
from collections import namedtuple

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt
from PIL import Image
from numpy import (sin, cos, exp, arcsin, arccos, arctan, arctan2, sqrt, floor,
                   pi, e, nan, isnan,
                   array, linspace, ones_like, zeros, average, all)

Patch = namedtuple('Patch', ['points', 'faces'])
Point = namedtuple('Point', ['pid', 'x', 'y', 'z'])

def ansi(n, bold=False):
    "Return function that escapes text with ANSI color n."
    return lambda txt: '\x1b[%d%sm%s\x1b[0m' % (n, ';1' if bold else '', txt)

black, red, green, yellow, blue, magenta, cyan, white = map(ansi, range(30, 38))
blackB, redB, greenB, yellowB, blueB, magentaB, cyanB, whiteB = [
    ansi(i, bold=True) for i in range(30, 38)]


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
    add('--points', type=int, default=0,
        help='número de puntos a usar como máximo (o 0 para usar todos)')
    add('--scale', type=float, default=0.02,
        help='fracción de radio entre el punto más bajo y más alto')
    add('--caps', default='auto',
        help='ángulo (en grados) al que llegan los casquetes (o auto o none)')
    add('--logo-north', default='', help='fichero de imagen con el logo norte')
    add('--logo-south', default='', help='fichero de imagen con el logo sur')
    add('--no-meridian', action='store_true', help='no añadir meridiano 0')
    add('--protrusion', type=float, default=1.02,
        help='fracción en la que sobresalen meridiano y casquetes del máximo')
    add('--no-ratio-check', action='store_true',
        help='no arreglar el ratio alto/ancho en ciertas proyecciones')
    add('--fix-gaps', action='store_true',
        help='intenta rellenar los huecos en el mapa')
    return parser


def process(args):
    if not os.path.isfile(args.image):
        sys.exit('File %s does not exist.' % args.image)

    check_caps(args.caps)

    output = args.output or '%s.%s' % (args.image.rsplit('.', 1)[0], args.type)
    if not args.overwrite:
        check_if_exists(output)

    print(green('Processing file %s ...' % args.image))
    img = Image.open(args.image)

    if args.fix_gaps:
        img = fill_dark(img)

    if not args.no_ratio_check:
        img = fix_ratios(img, args.projection)

    heights = get_heights(img, args.channel)
    if args.invert:
        heights = -heights

    if args.projection in ['mollweide', 'sinusoidal'] and args.caps == 'auto':
        caps = 'none'
    else:
        caps = args.caps

    projection_args = {'ptype': args.projection,
                       'npoints': args.points,
                       'scale': args.scale,
                       'caps': caps,
                       'meridian': not args.no_meridian,
                       'protrusion': args.protrusion}

    if args.type == 'asc':
        patches = get_patches(heights, projection_args,
                              args.logo_north, args.logo_south, add_faces=False)
        write_asc(output, patches)
    elif args.type == 'ply':
        patches = get_patches(heights, projection_args,
                              args.logo_north, args.logo_south)
        write_ply(output, patches)

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
            print(red('You say this image is a %s projection? The ratios '
                      'do not look good (%dx%d).\nChanging them to %dx%d. '
                      'Consider fixing the original.' % (ptype, nx, ny, nx,
                                                         ny_expected)))
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


def get_patches(heights, projection_args, logo_north, logo_south, add_faces=True):
    "Return a list of the patches (points and faces) that form the figure"
    patches = []

    protrusion = projection_args['protrusion'] * (1 + projection_args['scale'] / 2)
    caps = projection_args['caps']
    phi_cap = get_phi_cap(caps, heights, projection_args['ptype'])

    get_pid = lambda: patches[-1].points[-1][-1].pid + 1 if patches else 0

    # Logo / North cap.
    if logo_north:
        patch = get_logo_patch(logo_north, phi_cap, protrusion,
                               pid=get_pid(), add_faces=add_faces)
        patches.append(patch)
    elif caps != 'none':
        patch = get_cap_patch(phi_cap, protrusion,
                              pid=get_pid(), add_faces=add_faces)
        patches.append(patch)

    # Map.
    patch = get_map_patch(heights, projection_args,
                          pid=get_pid(), add_faces=add_faces)
    if add_faces and patches:
        row_previous = points_at_z_extreme(patches[-1].points, extreme='min')
        faces = get_faces([row_previous, patch.points[0]])
        patches.append(Patch([], faces))
    patches.append(patch)

    # South cap.
    if logo_south:
        patch = get_logo_patch(logo_south, -phi_cap, protrusion,
                               pid=get_pid(), add_faces=add_faces)
        if add_faces and patches:
            row = points_at_z_extreme(patch.points, extreme='max')
            faces = get_faces([patches[-1].points[-1], row])
            patches.append(Patch([], faces))
        patches.append(patch)
    elif caps != 'none':
        patch = get_cap_patch(-phi_cap, protrusion,
                              pid=get_pid(), add_faces=add_faces)
        if add_faces and patches:
            faces = get_faces([patches[-1].points[-1], patch.points[0]])
            patches.append(Patch([], faces))
        patches.append(patch)

    return patches


def points_at_z_extreme(points, extreme='max'):
    "Return a list of points that correspond to the boundary of the given ones"
    class OrderedPoint:  # will use for sorting in theta order
        def __init__(self, pid, x, y, z):
            self.pid = pid
            self.x = x
            self.y = y
            self.z = z
            self.theta = arctan2(y, x)

        def __lt__(self, p):
            theta = arctan2(p.y, p.x)
            return self.theta < theta

    points_flat = array([p for row in points for p in row])

    # Normalize points (make them have r=1).
    for i in range(len(points_flat)):
        pid, x, y, z = points_flat[i]
        r = sqrt(x*x + y*y + z*z)
        points_flat[i] = [pid, x / r, y / r, z / r]

    if extreme == 'min':
        zmin = points_flat[:,-1].min() + 1e-6
        points_border = [OrderedPoint(pid, x, y, z)
                            for pid, x, y, z in points_flat if z < zmin]
    elif extreme == 'max':
        zmax = points_flat[:,-1].max() - 1e-6
        points_border = [OrderedPoint(pid, x, y, z)
                            for pid, x, y, z in points_flat if z > zmax]
    else:
        raise ValueError('extreme must be either min or max')

    return [Point(int(p.pid), p.x, p.y, p.z) for p in sorted(points_border)]


def get_map_patch(heights, projection_args, pid=0, add_faces=True):
    "Return patch (points, faces) containing the map"
    print(blue('Adding map...'))
    points = get_map_points(heights, pid=pid, **projection_args)
    faces = get_faces(points) if add_faces else []
    return Patch(points, faces)


def get_cap_patch(phi_cap, protrusion, pid=0, add_faces=True):
    "Return patch (points, faces) containing the cap"
    print(blue('Adding %s cap...' % ('north' if phi_cap > 0 else 'south')))
    points = get_cap_points(protrusion, phi_max=phi_cap, pid=pid)
    faces = get_faces(points) if add_faces else []
    return Patch(points, faces)


def get_logo_patch(logo, phi_cap, protrusion, pid=0, add_faces=True):
    "Return patch (points, faces) containing the logo"
    print(blue('Adding logo...'))
    if not os.path.isfile(logo):
        sys.exit('File %s does not exist.' % logo)
    img = Image.open(logo)
    heights_logo = get_heights(img)
    points = get_logo_points(heights_logo, phi_max=phi_cap,
                             protrusion=protrusion, pid=pid)
    faces = get_faces(points) if add_faces else []
    return Patch(points, faces)


def write_ply(fname, patches):
    nvertices = patches[-1].points[-1][-1].pid + 1 if patches else 0

    with open(fname, 'wb') as fout:
        all_points, all_faces = zip(*patches)
        fout.write(ply_header(nvertices=nvertices,
                              nfaces=sum(len(x) for x in all_faces)))
        for points in all_points:
            write_vertices(fout, points)
        for faces in all_faces:
            write_faces(fout, faces)


def ply_header(nvertices, nfaces, binary=True):
    "Return header of a ply file with the given number of vertices and faces"
    return b"""\
ply
format %s 1.0
comment made by mapelia
element vertex %d
property float x
property float y
property float z
element face %d
property list uchar int vertex_index
end_header
""" % (b'binary_little_endian' if binary else b'ascii', nvertices, nfaces)


def write_vertices(fout, points, binary=True):
    "Write in fout the tuples of x, y, z that define the vertices"
    if binary:
        write = lambda x, y, z: fout.write(struct.pack(b'<3f', x, y, z))
    else:
        write = lambda x, y, z: fout.write(b'%g %g %g\n' % (x, y, z))

    for row in points:
        for p, x, y, z in row:
            write(x, y, z)


def write_faces(fout, faces, binary=True, invert=False):
    "Write in fout the lists of indices that define the faces"
    if not invert:
        reorder = lambda f: f
    else:
        reorder = lambda f: (f[0], f[2], f[1])

    if binary:
        write = lambda f: fout.write(struct.pack(b'<B3i', 3, *reorder(f)))
    else:
        write = lambda f: fout.write(b'3 %d %d %d\n' % reorder(f))

    for f in faces:
        write(f)


def write_asc(fname, patches):
    "Write an asc file with the points in the given patches"
    with open(fname, 'wb') as fout:
        for patch in patches:
            write_vertices(fout, patch.points, binary=False)


def get_map_points(heights, pid, ptype, npoints,
                   scale, caps, meridian, protrusion):
    "Return points on a sphere, modulated by the given heights"
    # The points returned look like a list of rows:
    # [[(0, x0_0, y0_0, z0_0), (1, x0_1, y0_1, z0_1), ...],
    #  [(n, x1_0, y1_0, z1_0), (n+1, x1_1, y1_1, z1_1), ...],
    #  ...]
    # This will be useful later on to connect the points and form faces.
    print('- Projecting heights on a sphere...')

    ny, nx = heights.shape
    get_theta, get_phi = projection_functions(ptype, nx, ny)
    points = []

    phi_cap = get_phi_cap(caps, heights, ptype)

    # Points from the given heights.
    hmin, hmax = heights.min(), heights.max()
    if hmax - hmin > 0.01:
        radii = 1.0 + scale * (2.0 * (heights - hmin) / (hmax - hmin) - 1.0)
    else:
        radii = ones_like(heights)
        meridian = False  # hack

    rmeridian = 1 + protrusion * scale

    n = sqrt(npoints)
    stepy = int(max(1, ny / (3 * n))) if n > 0 else 1
    # the 3 factor is related to 1/cos(phi)

    for j in range(0, ny, stepy):
        y_map = ny // 2 - j
        phi = get_phi(y_map)
        if isnan(phi) or abs(phi) > phi_cap:
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

            if meridian and -0.02 < theta < 0.02:
                r = rmeridian
            else:
                r = radii[j, i]

            x = r * cos(theta) * cphi
            y = r * sin(theta) * cphi
            z = r * sphi
            row.append(Point(pid, x, y, z))
            pid += 1
        if row:
            points.append(row)

    return points


def get_logo_points(heights, phi_max, protrusion=1, pid=0):
    "Return list of rows with the points from the logo in fname"
    print('- Projecting logo...')
    # phi_max > 0 for the north cap, < 0 for the south one.
    sign_phi = 1 if phi_max > 0 else -1
    abs_phi_max = abs(phi_max)

    ny, nx = heights.shape
    points = []
    N_2, nx_2, ny_2 = max(nx, ny) / 2, nx / 2, ny / 2
    for j in range(ny):
        row = []
        for i in range(nx):
            dist = sqrt( (i - nx_2)**2 + (j - ny_2)**2 ) / N_2
            if dist > 1:
                continue  # only values inside the circle
            r = protrusion + (protrusion - 1) * heights[j, i] / heights.max()
            theta = sign_phi * arctan2(ny_2 - j, i - nx_2)
            phi = sign_phi * (pi / 2 - (pi / 2 - abs_phi_max) * dist)

            x = r * cos(theta) * cos(phi)
            y = r * sin(theta) * cos(phi)
            z = r * sin(phi)
            row.append(Point(pid, x, y, z))
            pid += 1
        if len(row) > 1:  # we want at least 2 points in a row
            points.append(row)
        else:
            pid -= len(row)  # we didn't add it, so don't count it
    return points


def mod(x, y):
    "Return the representative of x between -y/2 and y/2 for the group R/yR"
    x0 = x - y * floor(x / y)
    return x0 if x0 < y / 2 else x0 - y


def get_cap_points(r, phi_max, pid):
    "Return lists of points that form the cap of radii r and from angle phi_max"
    rcphin, rsphin = r * cos(phi_max), r * sin(phi_max)
    if phi_max > 0:
        phi_start, phi_end, limit = pi / 2, phi_max, r
    else:
        phi_start, phi_end, limit = phi_max, -pi / 2, -r
    points = []
    for phi in linspace(phi_start, phi_end, 10):
        row = []
        rcphi, rsphi = r * cos(phi), r * sin(phi)
        z = rsphi
        for theta in linspace(-pi, pi, max(9, int(100 * cos(phi)))):
            x = cos(theta) * rcphi
            y = sin(theta) * rcphi
            row.append(Point(pid, x, y, z))
            pid += 1
        points.append(row)
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


def get_phi_cap(caps, heights, ptype):
    "Return the angle at which the cap ends"
    if caps == 'auto':
        ny, nx = heights.shape
        get_theta, get_phi = projection_functions(ptype, nx, ny)
        return get_phi(ny // 2)
    elif caps == 'none':
        return pi / 2
    else:  # caps is an angle then
        return pi / 2 - pi * float(caps) / 180


def get_faces(points):
    "Return faces as triplets of point indices"
    # points must be a list of rows, each containing the actual points
    # that correspond to a (closed!) section of an object.
    print('- Forming faces...')

    # This follows the "walking the dog" algorithm that I just made up.
    # It seems to work fine when using the points of a sphere...

    def dist2(p0, p1):  # geometric distance (squared) between two points
        _, x0, y0, z0 = p0[:4]
        _, x1, y1, z1 = p1[:4]
        r0 = sqrt(x0*x0 + y0*y0 + z0*z0)
        r1 = sqrt(x1*x1 + y1*y1 + z1*z1)
        # between points that have r=1, actually
        return (x1/r1 - x0/r0)**2 + (y1/r1 - y0/r0)**2 + (z1/r1 - z0/r0)**2

    # dog            <-- previous row
    #  ^
    #  i  ->  i+1    <-- current row
    # The position i (where the human is) is updated, and then the dog is
    # moved (in the previous row) until it cannot be closer to the human,
    # making triangles along the way. Then, a new triangle is made from the
    # current position to the next one and the dog (i -> i+1 -> dog).
    faces = []
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
                    faces.append((h()[0], dw()[0], d()[0]))
                    dog = dog_walking
                    dist = dist_new
                else:
                    break
            faces.append((h()[0], row_current[(i + 1) % len(row_current)][0], d()[0]))
        while dog != 0:  # we have to close the figure
            dog_walking = (dog + 1) % len(row_previous)
            faces.append((row_current[0][0], dw()[0], d()[0]))
            dog = dog_walking
    return faces


def fill_dark(img, too_dark_value=30, darkest_fill=50):
    "Fill dark values in the image (which correspond to areas with no data)"
    print('- Filling dark areas with nearby color...')
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


def get_heights(img, channel='val'):
    "Return an array with the heights extracted from the image"
    print('- Extracting heights from image (channel "%s")...' % channel)
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
