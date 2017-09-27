"""
Convierte imágenes con mapas a ficheros 3D.

Toma mapas de ficheros jpg, png, etc., y escribe ficheros ply (polígonos), asc
(nube de puntos) o stl (también polígonos) con una esfera que contiene las
elevaciones deducidas del mapa en cada punto. Estos ficheros se pueden a su vez
manipular con programas como MeshLab o Blender.
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

import sys
import os
from collections import namedtuple

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt
from PIL import Image
from numpy import arctan2, sqrt, pi, nan, array, zeros, average

try:
    from projections import (get_map_points, get_logo_points, get_cap_points,
                             get_phi_cap, get_faces, points_at_z_extreme)
except ImportError:
    sys.exit('projections module not ready. You may want to first run:\n'
             '  python3 setup.py build_ext --inplace')

from formats import write_ply, write_asc, write_stl

Patch = namedtuple('Patch', ['points', 'faces'])

def ansi(n, bold=False):
    "Return function that escapes text with ANSI color n"
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
    add('--type', choices=['ply', 'asc', 'stl'], default='ply',
        help='tipo de fichero a generar')
    add('--channel', default='val',
        choices=['r', 'g', 'b', 'average', 'hue', 'sat', 'val', 'color'],
        help='canal que contiene la información de la elevación')
    add('--invert', action='store_true', help='invierte las elevaciones')
    add('--projection', default='mercator',
        choices=['mercator', 'central-cylindrical', 'mollweide',
                 'equirectangular', 'sinusoidal'],
        help='tipo de proyección usada en el mapa')
    add('--points', type=int, default=0,
        help='número de puntos a usar como máximo (o 0 para usar todos)')
    add('--scale', type=float, default=0.02,
        help='fracción de radio entre el punto más bajo y más alto')
    add('--caps', default='auto',
        help='ángulo (en grados) al que llegan los casquetes (o auto o none)')
    add('--logo-north', default='', help='fichero de imagen con el logo norte')
    add('--logo-south', default='', help='fichero de imagen con el logo sur')
    add('--meridian', default='0',
        help='longitud (en grados) donde colocar el meridiano (o none)')
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
    check_meridian(args.meridian)

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
        heights = heights.max() - heights

    if args.projection in ['mollweide', 'sinusoidal'] and args.caps == 'auto':
        caps = 'none'
    else:
        caps = args.caps

    meridian = pi * float(args.meridian) / 180 if args.meridian != 'none' else nan

    projection_args = {'ptype': args.projection,
                       'npoints': args.points,
                       'scale': args.scale,
                       'caps': caps,
                       'meridian': meridian,
                       'protrusion': args.protrusion}

    if args.type == 'asc':
        patches = get_patches(heights, projection_args,
                              args.logo_north, args.logo_south, add_faces=False)
        write_asc(output, patches)
    elif args.type == 'ply':
        patches = get_patches(heights, projection_args,
                              args.logo_north, args.logo_south)
        write_ply(output, patches)
    elif args.type == 'stl':
        patches = get_patches(heights, projection_args,
                              args.logo_north, args.logo_south)
        write_stl(output, patches)

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


def check_meridian(meridian):
    "Check that the meridian is valid"
    # We want this so as to fail early.
    try:
        if not -180 <= float(meridian) <= 180:
            sys.exit('meridian can be an angle between -180 and 180 (or none).')
    except ValueError:
        if meridian != 'none':
            sys.exit('meridian can be "none" or a float.')


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
        imx = array(img.convert('RGBA'), dtype=float)
        if   channel == 'r':  return imx[:,:,0]
        elif channel == 'g':  return imx[:,:,1]
        elif channel == 'b':  return imx[:,:,2]
        elif channel == 'average':
            return average(imx, axis=2)
    elif channel in ['hue', 'sat', 'val']:
        # These channels are straigthforward: higher values are higher heights.
        imxHSV = array(img.convert('RGBA').convert('HSV'), dtype=float)
        if   channel == 'hue':  return imxHSV[:,:,0]
        elif channel == 'sat':  return imxHSV[:,:,1]
        elif channel == 'val':  return imxHSV[:,:,2]
    elif channel == 'color':
        # This channel is *not* straigthforward.
        rgb2height = find_rgb2height(img)
        nx, ny = img.size
        heights = zeros((ny, nx), dtype=float)
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
