"""
Functions to create 3D files in the following formats: ply, asc, stl.
"""

import struct


def write_ply(fname, patches):
    "Create ply file fname with the points and faces in patches"
    nvertices = patches[-1].points[-1][-1].pid + 1 if patches else 0
    all_points, all_faces = zip(*patches)

    with open(fname, 'wb') as fout:
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


def write_stl(fname, patches, invert=False):
    "Create stl file fname with the triangles in patches"
    all_points, all_faces = zip(*patches)
    points_flat = [(p.x, p.y, p.z) for points in all_points
                                   for row in points for p in row]

    order = (0, 1, 2) if not invert else (0, 2, 1)

    with open(fname, 'wb') as fout:
        write = lambda *args: fout.write(struct.pack(*args))

        write('<80B', *tuple([0] * 80))  # header (empty)
        write('<I', sum(len(x) for x in all_faces))  # number of triangles
        for faces in all_faces:
            for f in faces:
                p0, p1, p2 = [points_flat[f[i]] for i in order]
                write('<3f', 0, 0, 0)  # normal vector (empty)
                write('<3f', *p0)  # vertex 1
                write('<3f', *p1)  # vertex 2
                write('<3f', *p2)  # vertex 3
                write('<H', 0)  # attribute byte count (empty)
