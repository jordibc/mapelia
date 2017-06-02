#!/usr/bin/env python3

"""
Tests/ejemplos relacionados con mapas.

Este fichero no es necesario para ejecutar mapelia, pero me sirve para
probar cosas relacionadas con lo que quiero hacer en el programa principal.
"""

from PIL import Image
import numpy as np


def write_ply():
    points = sphere_rows()
    #points = plane_rows()

    nvertex = points[-1][-1][0] + 1  # sum(map(len, points))
    faces = list(get_faces(points))
    with open('sphere.ply', 'wt') as fout:
        fout.write("""\
ply
format ascii 1.0
element vertex %d
property float x
property float y
property float z
element face %d
property list uint8 int32 vertex_index
end_header
""" % (nvertex, len(faces)))
        for row in points:
            for p, x, y, z in row:
                fout.write('%g %g %g\n' % (x, y, z))
        for f in faces:
            fout.write('3 %d %d %d\n' % f)


def get_faces(points):
    "Yield faces as triplets of point indices"
    # points must be a list of rows, each containing the actual points
    # that correspond to a (closed!) section of an object.
    def dist2(p0, p1):
        _, x0, y0, z0 = p0
        _, x1, y1, z1 = p1
        return (x1 - x0)**2 + (y1 - y0)**2 + (z1 - z0)**2

    # h
    # b l
    for j in range(1, len(points)):
        row_current = points[j]
        row_previous = points[j - 1]
        hoagie = 0
        for i in range(len(row_current)):
            bernard = i
            laverne = (i + 1) % len(row_current)
            hoagie_start = hoagie
            hoagie_walking = hoagie
            dbh = dist2(row_current[bernard], row_previous[hoagie_walking])
            while True:
                hoagie_walking = (hoagie_walking + 1) % len(row_previous)
                d = dist2(row_current[bernard], row_previous[hoagie_walking])
                if d < dbh:
                    yield (row_current[bernard][0], row_previous[hoagie][0], row_previous[hoagie_walking][0])
                    hoagie = hoagie_walking
                    dbh = d
                else:
                    break
            yield (row_current[bernard][0], row_previous[hoagie][0], row_current[laverne][0])
        yield (row_current[0][0], row_previous[hoagie][0], row_previous[0][0])


def plane_rows():
    points = []
    n = 0
    for y in np.arange(2, -2, -0.5):
        row = []
        for x in np.arange(-2, 2, 0.5):
            row.append((n, x, y, 0))
            n += 1
        points.append(row)
    return points


def sphere_rows():
    points = []
    n = 0
    for phi in np.arange(-np.pi/2, np.pi/2, 0.01):
        row = []
        #for theta in np.arange(-np.pi, np.pi, 0.1):
        for theta in np.linspace(-np.pi, np.pi, max(5, int(200 * np.cos(phi)))):
            x = np.cos(theta) * np.cos(phi)
            y = np.sin(theta) * np.cos(phi)
            z = np.sin(phi)
            row.append((n, x, y, z))
            n += 1
        points.append(row)
    return points


def sphere():
    for phi in np.arange(-np.pi/2, np.pi/2, 0.2):
        for theta in np.arange(-np.pi, np.pi, 0.2):
            x = np.cos(theta) * np.cos(phi)
            y = np.sin(theta) * np.cos(phi)
            z = np.sin(phi)
            yield (x, y, z)

def write_sphere_asc():
    "Write file sphere.asc with points of a sphere"
    with open('sphere.asc', 'wt') as fout:
        for xyz in sphere():
            fout.write('%g %g %g\n' % xyz)


def create_hue_image():
    "Return an image with hue lines"
    nx, ny = (1024, 720)
    img = Image.new('HSV', (nx, ny))
    for i in range(nx):
        hue = min(i // 4, 256)
        for j in range(ny):
            img.putpixel((i, j), (hue, 250, 200))
    return img.convert('RGB')


def get_rgb_values(img):
    "Return set of rgb vales in image"
    nx, ny = img.size
    values = set()
    for i in range(nx):
        for j in range(ny):
            values.add(img.getpixel((i, j)))
    return values


# Experimenting with palette.tab, I get what must be the order.
# Form get_values(....'source/2000.jpg'...) I get the possible colors.
# To find out the heights, I suppose the order is the same as the one
# I found in palette.tab.

def palette_test():
    "Return an image with lines of the palette from palette.tab"
    nx, ny = (1024, 720)
    img = Image.new('HSV', (nx, ny))
    palette_file = ('pds-geosciences.wustl.edu/mgn/mgn-v-gxdr-v1/mg_3002/gsdr/'
                    'merc/palette.tab')
    get_rgb = lambda line: tuple(map(int, line.split()[1:]))
    rgbs = [get_rgb(line) for line in open(palette_file)]
    for i in range(nx):
        level = min(i // 4, 255)
        for j in range(ny):
            img.putpixel((i, j), rgbs[level])
    return img


def print_palette_hsv():
    "Print hue,saturation,value for the colors specified in palette.tab"
    palette_file = ('pds-geosciences.wustl.edu/mgn/mgn-v-gxdr-v1/mg_3002/gsdr/'
                    'merc/palette.tab')
    rs = Image.new('L', (1, 256))
    gs = Image.new('L', (1, 256))
    bs = Image.new('L', (1, 256))
    imgRGB = Image.new('RGB', (1, 256))
    for i, line in enumerate(open(palette_file)):
        imgRGB.putpixel((0, i), tuple(map(int, line.split()[1:])))
    imgHSV = imgRGB.convert('HSV')

    for i in range(256):
        print('%d %d %d' % imgHSV.getpixel((0, i)))

# The order seems to be:
# -H, V


def rgb2gray(img):
    "Return image whose grayscale values correspond to the average rgb in img"
    values = np.average(img, axis=2)
    return Image.fromarray(values).convert('RGB')


def rgb2gray_slow(img):
    "Return image whose grayscale values correspond to the red-to-blue in img"
    values = get_values(img)  # TODO: should we normalize?
    imgL = img.convert('L')
    nx, ny = img.size
    for i in range(nx):
        for j in range(ny):
            imgL.putpixel((i, j), (values[i, j],))
    return imgL
    # I wrote this version before knowing you could do it so nicely
    # and fast in a different way...


def get_values(img):
    "Return array with the red-to-blue values of the given image"
    values = np.zeros(img.size, dtype=np.int8)
    nx, ny = img.size
    for i in range(nx):
        for j in range(ny):
            r, g, b = img.getpixel((i, j))
            values[i, j] = (r + g + b) / 3
    return values
    # This is intended to undo the heigth->color transformation from the
    # original map, but, what is actually the original transformation?


def hue2gray(img):
    "Return an image whose grayscale values correspond to the hues in img"
    hues = get_hues(img)
    imgL = img.convert('L')
    nx, ny = img.size
    for i in range(nx):
        for j in range(ny):
            imgL.putpixel((i, j), (hues[i, j],))
    return imgL


def get_hues(img):
    "Return array with the hue values of the given image"
    return np.array(img.convert('HSV'))[:,:,0]


def get_hues_slow(img):
    "Return array with the hue values of the given image"
    hues = np.zeros(img.size, dtype=np.int)
    imgHSV = img.convert('HSV')
    nx, ny = img.size
    for i in range(nx):
        for j in range(ny):
            hues[i, j] = imgHSV.getpixel((i, j))[0]
    return hues
    # I wrote this version before knowing you could do it so nicely
    # and fast in a different way...
