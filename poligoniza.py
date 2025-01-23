#!/usr/bin/env python3

"""
Create a file of polygons (.ply or .stl) from one with only the 3D points
(.asc).

The original asc file must have the points in the order that corresponds to
the sections of a quasi-spherical object.
"""

import sys
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt

import maps
try:
    import projections
    assert projections.__version__ == '1.3.0'
except (ImportError, AssertionError, AttributeError) as e:
    sys.exit('projections module not ready. You may want to first run:\n'
             '  %s setup.py build_ext --inplace' % sys.executable)
import formats
import asc


def main():
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut
    add('file', help='asc file with the points coordinates')
    add('-o', '--output', default='',
        help='output file (if empty, it is generated from the image file name)')
    add('--overwrite', action='store_true',
        help='do not check if the output file already exists')
    add('--type', choices=['ply', 'stl'], default='ply',
        help='type of 3D file to generate')
    add('--ascii', action='store_true',
        help='write the resulting ply file in ascii')
    add('--invert', action='store_true',
        help='invert the orientations of the faces')
    add('--row-length', type=int, default=0,
        help='maximum number of points to use (or 0 to autodetect)')
    args = parser.parse_args()

    output = args.output or '%s.%s' % (args.file.rsplit('.', 1)[0], args.type)
    if not args.overwrite:
        maps.check_if_exists(output)

    print(maps.green('Processing file %s ...' % args.file))
    points_raw = asc.get_points_raw(args.file)
    points = asc.get_points(points_raw, args.row_length)
    faces = projections.get_faces(points)

    if args.type == 'ply':
        with open(output, 'wb') as fout:
            binary = not args.ascii
            fout.write(formats.ply_header(nvertices=len(points_raw),
                                          nfaces=len(faces), binary=binary))
            formats.write_vertices(fout, points, binary)
            formats.write_faces(fout, faces, binary, args.invert)
    elif args.type == 'stl':
        patches = [(points, faces)]
        formats.write_stl(output, patches, args.invert)
    print('The output is in file %s' % output)



if __name__ == '__main__':
    main()
