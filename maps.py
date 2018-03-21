"""
Transform images with maps into 3D files.

It takes maps images in jpg, png and so on, and writes 3D polygon files
(ply and stl) or clouds of 3D points (asc) with a sphere that contains the
elevations deduced from the map at each point. These files can be further
processed with programs like MeshLab or Blender.
"""

# Spherical coordinates convention:
#   theta: angle from the x axis to the projection of the point in the xy plane
#   phi: angle from the xy plane to the point
# That is, theta is the longitude and phi is the latitude:
#   x = r * cos(theta) * cos(phi)
#   y = r * sin(theta) * cos(phi)
#   z = r * sin(phi)

# TODO:
# * Create test image maps with simple lines or patterns and see if they
#   are distorted when creating the 3d model.
# * Allow the use of an external 1xN image with the colors that
#   correspond to different heights.
# * Add option to remove parallels and meridians in the original image.

import sys
import os
from collections import namedtuple

import argparse as ap
from configparser import ConfigParser, ParsingError
import colorsys
from PIL import Image
from numpy import cos, sqrt, pi, array, zeros, average

try:
    import projections as pj
    assert pj.__version__ == '1.2.0'
except (ImportError, AssertionError, AttributeError) as e:
    sys.exit('projections module not ready. You may want to first run:\n'
             '  %s setup.py build_ext --inplace' % sys.executable)

from formats import write_ply, write_asc, write_stl

Patch = namedtuple('Patch', ['points', 'faces'])
Logo = namedtuple('Logo', ['image', 'scale'])

def ansi(n, bold=False):
    "Return function that escapes text with ANSI color n"
    return lambda txt: '\x1b[%d%sm%s\x1b[0m' % (n, ';1' if bold else '', txt)

black, red, green, yellow, blue, magenta, cyan, white = map(ansi, range(30, 38))
blackB, redB, greenB, yellowB, blueB, magentaB, cyanB, whiteB = [
    ansi(i, bold=True) for i in range(30, 38)]


def get_parser():
    "Return the parser object with all the arguments"
    parser = ap.ArgumentParser(description=__doc__, allow_abbrev=False,
                               formatter_class=ap.ArgumentDefaultsHelpFormatter)
    add = parser.add_argument  # shortcut
    add('image', help='image file with the map')
    add('--output', default='',
        help='output file (if empty, it is generated from the image file name)')
    add('--overwrite', action='store_true',
        help='do not check if the output file already exists')
    add('--type', choices=['ply', 'asc', 'stl'], default='ply',
        help='type of 3D file to generate')
    add('--channel', default='val',
        choices=['r', 'g', 'b', 'average', 'hue', 'sat', 'val', 'color'],
        help='channel with the elevations information in the image')
    add('--invert', action='store_true', help='invert heights')
    add('--projection', default='mercator',
        choices=['mercator', 'central-cylindrical', 'mollweide',
                 'equirectangular', 'sinusoidal'],
        help='projection used in the map')
    add('--points', type=int, default=0,
        help='maximum number of points to use (or 0 to use all in the image)')
    add('--scale', type=float, default=0.02,
        help='fraction of radius between the highest and lowest points')
    add('--caps', default='auto',
        help='angle (in degrees) where the caps end (or auto or none)')
    add('--caps-height', type=float, default=1.02,
        help='height of the caps (1 would be at sea-level)')
    add('--logo-north', default='', help='image file with the north logo')
    add('--logo-north-scale', type=float, default=1.0,
        help='scale factor for the north logo (can be < 0 for engravings)')
    add('--logo-south', default='', help='image file with the south logo')
    add('--logo-south-scale', type=float, default=1.0,
        help='scale factor for the south logo (can be < 0 for engravings)')
    add('--meridians-pos', nargs='*', metavar='POSITION', type=float, default=[0],
        help='list of longitudes (in degrees) with meridians')
    add('--meridians-widths', nargs='*', metavar='WIDTH', type=float, default=[2],
        help='list of widths (in degrees) of the meridians')
    add('--meridians-height', type=float, default=1.02,
        help='elevation of the meridians (at the equator)')
    add('--equator-width', type=float, default=0,
        help='width (in degrees) of the equator (0 for no equator)')
    add('--equator-height', type=float, default=1.02,
        help='elevation of the equator')
    add('--thickness', type=float, default=1,
        help='thickness of the generated object (< 1 for partially hollow))')
    add('--no-ratio-check', action='store_true',
        help='do not fix the height/width ratio for certain projections')
    add('--blur', type=float, default=0,
        help='amount of pixels used to smooth the image')
    add('--fix-gaps', action='store_true',
        help='try to fill the gaps in the map')
    add('--config', default='', help='file with default parameters')
    return parser


def process(args):
    "Create a 3d file from an image and return its name"
    if not os.path.isfile(args.image):
        sys.exit('File %s does not exist.' % args.image)

    print(green('Processing file %s (projection %s) ...' %
                (args.image, args.projection)))

    if args.config:
        try:
            cfg = read_config(args.config)
            check_config(cfg, args)
            update_args(args, cfg)
        except (FileNotFoundError, AssertionError,
                ValueError, ParsingError) as e:
            sys.exit('Error in file %s: %s' % (args.config, e))

    check_caps(args.caps)
    check_meridians(args.meridians_pos, args.meridians_widths)

    output = args.output or '%s.%s' % (args.image.rsplit('.', 1)[0], args.type)
    if not args.overwrite:
        check_if_exists(output)

    img = Image.open(args.image)

    if args.fix_gaps:
        img = fill_dark(img)

    if not args.no_ratio_check:
        img = fix_ratios(img, args.projection)

    if args.blur > 0:
        img = blur(img, args.blur, args.projection)

    heights = get_heights(img, args.channel)
    if args.invert:
        heights = heights.max() - heights

    if args.projection in ['mollweide', 'sinusoidal'] and args.caps == 'auto':
        caps = 'none'
    else:
        caps = args.caps

    meridians = [(deg2rad(pos), deg2rad(width)) for pos, width in
                 zip(args.meridians_pos, args.meridians_widths)]

    projection_args = {'ptype': args.projection,
                       'npoints': args.points,
                       'scale': args.scale,
                       'caps': caps,
                       'caps_height': args.caps_height,
                       'meridians': meridians,
                       'meridians_height': args.meridians_height,
                       'equator_width': deg2rad(args.equator_width),
                       'equator_height': args.equator_height}

    logo_args = {'north': Logo(args.logo_north, args.logo_north_scale),
                 'south': Logo(args.logo_south, args.logo_south_scale)}

    add_faces = args.type in ['ply', 'stl']

    patches = get_patches(heights, projection_args, logo_args, args.thickness,
                          add_faces)

    write = {'asc': write_asc,
             'ply': write_ply,
             'stl': write_stl}[args.type]
    write(output, patches)

    return output


def read_config(fname):
    "Return dict with the parameters read from configuration file fname"
    print(blue('Reading defaults from config file %s ...' % fname))
    cp = ConfigParser()
    cp.read_file(open(fname))
    assert 'mapelia' in cp, 'Missing section [mapelia]'
    return cp['mapelia']


def check_config(cfg, args):
    "Assert all the keys in configuration dict cfg exist in args"
    valid_keys = dict(args._get_kwargs()).keys() - {'image', 'config'}
    for key in cfg:
        assert key.replace('-', '_') in valid_keys, 'Unknown option "%s"' % key


def update_args(args, cfg):
    "Modify args with the contents of config dict cfg"
    converters = get_arguments_converters()
    used_keys = {x[2:] for x in sys.argv if x.startswith('--')}
    for key in cfg.keys() - used_keys:
        cast = converters.get(key, lambda x: x)
        value = cast(cfg[key])
        print('- Setting %s to %s' % (key, value))
        setattr(args, key.replace('-', '_'), value)


def get_arguments_converters():
    "Return dict {argname: converter} with converter functions for known args"
    def list_of_floats(txt):
        return [float(x) for x in txt.split()]
    def truth(txt):
        assert txt.lower() in ['true', 'yes', 'false', 'no'], \
            'Invalid value "%s" (valid values: "true", "false")' % txt
        return txt.lower() in ['true', 'yes']
    return {
        'points': int, 'scale': float, 'thickness': float, 'blur': float,
        'logo-north-scale': float, 'logo-south-scale': float,
        'caps-height': float, 'meridians-height': float,
        'equator-width': float, 'equator-height': float,
        'meridians-pos': list_of_floats, 'meridians-widths': list_of_floats,
        'overwrite': truth, 'invert': truth, 'no-ratio-check': truth,
        'fix-gaps': truth}


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


def check_meridians(meridians_pos, meridians_widths):
    "Check that the meridians are valid"
    # We want this so as to fail early.
    try:
        assert len(meridians_pos) == len(meridians_widths), \
            ('--meridians-pos and --meridians-widths must have the same number '
             'of elements (now %s vs %s).' % (meridians_pos, meridians_widths))
        for pos in meridians_pos:
            assert -180 <= pos <= 180, \
                'Meridian %g should be between -180 and 180.' % pos
        for width in meridians_widths:
            assert 0 < width < 360, \
                'Width %g should be between 0 and 360.' % width
    except AssertionError as e:
        sys.exit(e)


def check_if_exists(fname):
    if os.path.exists(fname):
        try:
            answer = input('File %s already exists. Overwrite? [y/n] ' % fname)
            assert answer.lower().startswith('y')
        except (KeyboardInterrupt, AssertionError):
            sys.exit('\nCancelling.')


def get_patches(heights, projection_args, logo_args, thickness, add_faces=True):
    "Return a list of the patches (points and faces) that form the figure"
    patches = []

    caps = projection_args['caps']
    caps_height = projection_args['caps_height']
    phi_cap = pj.get_phi_cap(caps, heights, projection_args['ptype'])

    get_pid = lambda: patches[-1].points[-1][-1].pid + 1 if patches else 0

    # Logo / North cap.
    if logo_args['north'].image:
        patch = get_logo_patch(logo_args['north'], phi_cap, caps_height,
                               pid=get_pid(), add_faces=add_faces)
        patches.append(patch)
        limiting_points = pj.points_at_extreme(patch.points)
    elif caps != 'none':
        patch = get_cap_patch(phi_cap, caps_height,
                              pid=get_pid(), add_faces=add_faces)
        patches.append(patch)
        limiting_points = patch.points[-1]

    # Map.
    patch = get_map_patch(heights, projection_args,
                          pid=get_pid(), add_faces=add_faces)
    if add_faces and patches:
        print(blue('Stitching patches...'))
        faces = pj.get_faces([limiting_points, patch.points[0]])
        patches.append(Patch([], faces))
    patches.append(patch)

    # South cap.
    if logo_args['south'].image:
        patch = get_logo_patch(logo_args['south'], -phi_cap, caps_height,
                               pid=get_pid(), add_faces=add_faces)
        if add_faces and patches:
            print(blue('Stitching patches...'))
            limiting_points = pj.points_at_extreme(patch.points)
            faces = pj.get_faces([patches[-1].points[-1], limiting_points])
            patches.append(Patch([], faces))
        patches.append(patch)
    elif caps != 'none':
        patch = get_cap_patch(-phi_cap, caps_height,
                              pid=get_pid(), add_faces=add_faces)
        if add_faces and patches:
            print(blue('Stitching patches...'))
            faces = pj.get_faces([patches[-1].points[-1], patch.points[0]])
            patches.append(Patch([], faces))
        patches.append(patch)

    # Inner sphere (to make the ball hollow).
    if 0 < thickness < 1:
        r = 1 - thickness
        patches.append(get_sphere_patch(r, pid=get_pid(), add_faces=add_faces))

    return patches


def get_map_patch(heights, projection_args, pid=0, add_faces=True):
    "Return patch (points, faces) containing the map"
    print(blue('Adding map...'))
    points = pj.get_map_points(heights, pid=pid, **projection_args)
    faces = pj.get_faces(points) if add_faces else []
    return Patch(points, faces)


def get_cap_patch(phi_cap, caps_height, pid=0, add_faces=True):
    "Return patch (points, faces) containing the cap"
    print(blue('Adding %s cap (latitude %g deg) ...' %
               (('north' if phi_cap > 0 else 'south'), 180 * phi_cap / pi)))
    points = pj.get_cap_points(caps_height, phi_max=phi_cap, pid=pid)
    faces = pj.get_faces(points) if add_faces else []
    return Patch(points, faces)


def get_sphere_patch(r, pid=0, add_faces=True):
    "Return patch (points, faces) containing the inner sphere"
    print(blue('Adding inner sphere (radius %g) ...' % r))
    points = pj.get_sphere_points(r, phi_start=pi/2, phi_end=-pi/2, pid=pid)
    faces = pj.invert(pj.get_faces(points)) if add_faces else []
    return Patch(points, faces)


def get_logo_patch(logo, phi_cap, caps_height, pid=0, add_faces=True):
    "Return patch (points, faces) containing the logo"
    print(blue('Adding logo from %s ...' % logo.image))
    if not os.path.isfile(logo.image):
        sys.exit('File %s does not exist.' % logo.image)
    img = Image.open(logo.image)
    heights_logo = get_heights(img)
    heights_logo /= heights_logo.max()
    heights_logo *= logo.scale
    points = pj.get_logo_points(heights_logo, phi_max=phi_cap,
                                caps_height=caps_height, pid=pid)
    faces = pj.get_faces(points, close_figure=False) if add_faces else []
    return Patch(points, faces)


def fill_dark(img, too_dark_value=30, darkest_fill=50):
    "Fill dark values in the image (which correspond to areas with no data)"
    print(blue('Filling dark areas with nearby color...'))
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
    print(blue('Extracting heights from image (channel "%s") ...' % channel))
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
        rgb2height = find_rgb_heights(img)
        nx, ny = img.size
        heights = zeros((ny, nx), dtype=float)
        for j in range(ny):
            for i in range(nx):
                heights[j, i] = rgb2height[img.getpixel((i, j))]
        return heights


def find_rgb_heights(img):
    "Return a dict to transform rgb(a) tuples to heights"
    # It is assumed that low heights correspond to big hues, and for
    # the same hue a lower color value corresponds to higher heights.
    def rank(rgb):
        r, g, b = rgb[:3]  # there may be an alpha channel -- if so, ignore it
        hue, sat, val = colorsys.rgb_to_hsv(r, g, b)
        return (-hue, val)
    rgbs = sorted(set(img.getdata()), key=rank)
    return {rgb: i for i, rgb in enumerate(rgbs)}


def blur(img, strength=2, projection='equirectangular'):
    "Return a blurred image"
    print(blue('Blurring image (strength %g) ...' % strength))
    # We'd love to do something as simple and fast as:
    #   return img.filter(ImageFilter.BLUR)
    # but we want it to wrap on the x axis and average more near the poles.
    nx, ny = img.size
    _, get_phi = pj.projection_functions(projection, nx, ny)

    imx = array(img.convert('RGBA'), dtype=float)
    imx_blurred = zeros(imx.shape, dtype='uint8')  # will be the image blurred
    for j in range(ny):
        y_map = ny // 2 - j
        cphi = abs(cos(get_phi(y_map))) + 1e-6  # abs() and 1e-6 are for safety
        dilation = (1 if projection in ['mollweide', 'sinusoidal'] else
                    max(1, 1 / cphi))
        di = min(ny // 4, int(strength * dilation))
        for i in range(nx):
            ri = [x if x < nx else x - nx for x in range(i - di, i + di + 1)]
            imx_blurred[j,i,:] = average(imx[j,ri,:], axis=0)
    return Image.fromarray(imx_blurred)


def deg2rad(x):
    return pi * x / 180
