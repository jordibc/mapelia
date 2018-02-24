"""
Projections-related functions for mapelia.

They are also the most computationally-intensive and thus can benefit
from using cython.
"""

# If you modify this file, you can recreate projections.c by running:
#   cython3 -a projections.pyx
# Then, you can create the python module with:
#   python3 setup.py build_ext --inplace

from collections import namedtuple

from numpy import (sin, cos, exp, arcsin, arccos, arctan, arctan2, sqrt,
                   pi, nan, isnan, ones_like, linspace, floor)

Point = namedtuple('Point', ['pid', 'x', 'y', 'z'])

red = lambda txt: '\x1b[31m%s\x1b[0m' % txt


def get_map_points(heights, long pid, ptype, npoints,
                   double scale, caps, meridians, double protrusion):
    "Return points on a sphere, modulated by the given heights"
    # The points returned look like a list of rows:
    # [[(0, x0_0, y0_0, z0_0), (1, x0_1, y0_1, z0_1), ...],
    #  [(n, x1_0, y1_0, z1_0), (n+1, x1_1, y1_1, z1_1), ...],
    #  ...]
    # This will be useful later on to connect the points and form faces.
    cdef double x, y, z, r, theta, phi

    print('- Projecting heights on a sphere...')

    ny, nx = heights.shape
    get_theta, get_phi = projection_functions(ptype, nx, ny)
    points = []

    phi_cap = get_phi_cap(caps, heights, ptype)
    if caps != 'none' and phi_cap > get_phi(ny // 2):
        print(red('Gap between caps and the map projection (cap ends at '
                  'latitude %g deg, but map highest is %g deg).\nIt may look '
                  'ugly. You probably want a different value for --caps.' %
                  (180 * phi_cap / pi, 180 * get_phi(ny // 2) / pi)))

    # Points from the given heights.
    hmin, hmax = heights.min(), heights.max()
    if hmax - hmin > 1e-6:
        radii = 1 + scale * (2 * (heights - hmin) / (hmax - hmin) - 1)
    else:
        radii = ones_like(heights)

    rmeridian = protrusion * (1 + scale / 2)

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

        min_meridian_width = 2 * pi * stepx / nx
        def touches_meridians(theta):
            dist = lambda x: abs(mod_2pi(theta - x))  # angular distance
            return any(dist(pos) <= max(width / 2, min_meridian_width)
                       for pos, width in meridians)

        for i in range(0, nx, stepx):
            x_map = i - nx // 2
            theta = get_theta(x_map, y_map)
            if isnan(theta):
                continue

            # TODO: make a nicer algorithm for the meridian, that
            # always puts it at the same place and interpolates the
            # last point before putting the triangles in the meridian.
            if touches_meridians(theta):
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


def get_logo_points(heights, double phi_max, double protrusion=1, long pid=0):
    "Return list of rows with the points from the logo in fname"
    cdef double x, y, z, r, theta, phi, dist, sign_phi, abs_phi_max

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
            r = protrusion + (protrusion - 1) * heights[j, i]
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


def get_cap_points(r, phi_max, pid):
    "Return lists of points that form the cap of radii r and from angle phi_max"
    if phi_max > 0:
        phi_start, phi_end = pi / 2, phi_max
    else:
        phi_start, phi_end = phi_max, -pi / 2
    return get_sphere_points(r, phi_start, phi_end, pid)


def get_sphere_points(double r, double phi_start, double phi_end, long pid):
    "Return lists of points on a sphere of radii r, from phi_start to phi_end"
    cdef double x, y, z, theta, phi

    nphi = max(10, 10 * abs(phi_end - phi_start))
    points = []
    for phi in linspace(phi_start, phi_end, nphi):
        row = []
        z = r * sin(phi)
        if abs(z - r) < 1e-6:  # we are at an extreme
            row.append(Point(pid, 0, 0, z))  # just put one point
            pid += 1
        else:
            rcphi = r * cos(phi)
            for theta in linspace(-pi, pi, max(9, int(100 * cos(phi)))):
                x = cos(theta) * rcphi
                y = sin(theta) * rcphi
                row.append(Point(pid, x, y, z))
                pid += 1
        points.append(row)
    return points


def get_phi_cap(caps, heights, ptype):
    "Return the angle at which the cap ends"
    if caps in ['auto', 'none']:
        ny, nx = heights.shape
        get_theta, get_phi = projection_functions(ptype, nx, ny)
        return get_phi(ny // 2)
        # If caps == 'none' that value will only be used for the logo.
    else:  # caps is an angle then
        return pi / 2 - pi * float(caps) / 180


def projection_functions(ptype, int nx, int ny):
    "Return functions to get theta, phi from x, y"
    cdef double r, x, y

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
    elif ptype == 'central-cylindrical':
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
        #   x = r * theta
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


def get_faces(points, close_figure=True):
    "Return faces as triplets of point indices"
    # points must be a list of rows, each containing the actual points
    # that correspond to a (closed!) section of an object.
    print('- Forming faces...')

    # This follows the "walking the dog" algorithm that I just made up.
    # It seems to work fine when using the points of a sphere...
    #
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
            point_norm_human = norm(h())
            dist = dist2(point_norm_human, norm(d()))
            while True:  # let the dog walk until it's as close as possible
                dog_walking = (dog_walking + 1) % len(row_previous)
                dist_new = dist2(point_norm_human, norm(dw()))
                if dist_new < dist:
                    faces.append((h().pid, dw().pid, d().pid))
                    dog = dog_walking
                    dist = dist_new
                else:
                    break
            # Triangle from the current position to the next one and the dog.
            if i + 1 < len(row_current):
                faces.append((h().pid, row_current[i + 1].pid, d().pid))
            elif close_figure:
                faces.append((h().pid, row_current[0].pid, d().pid))
        if close_figure:
            while dog != 0:  # we have to close the figure
                dog_walking = (dog + 1) % len(row_previous)
                faces.append((row_current[0].pid, dw().pid, d().pid))
                dog = dog_walking
    return faces


def norm(p):
    "Return a tuple with the components of point p normalized to r=1"
    cdef double x, y, z
    x, y, z = p[1:4]
    r = sqrt(x*x + y*y + z*z)
    return x/r, y/r, z/r


def dist2(p0, p1):
    "Return the geometric distance (squared) between two points"
    cdef double x0, y0, z0, x1, y1, z1
    x0, y0, z0 = p0
    x1, y1, z1 = p1
    dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
    return dx*dx + dy*dy + dz*dz


def points_at_extreme(points, sample_points=[]):
    "Return a list of points that correspond to the boundary of the given ones"
    def rxy(p):
        cdef double x, y
        _, x, y, _ = p
        return sqrt(x*x + y*y)

    sample_points = sample_points or points[1]
    rxy_limit = sum(rxy(p) for p in sample_points) / len(sample_points)

    return sorted((p for row in points for p in row if rxy(p) > rxy_limit),
                  key=lambda p: arctan2(p[2], p[1]))


def invert(faces):
    "Return a list of faces with the inverse orientation"
    inverted_faces = []
    for p0, p1, p2 in faces:
        inverted_faces.append((p0, p2, p1))
    return inverted_faces


def mod_2pi(double a):
    "Return the equivalent to angle a in [-pi, pi)"
    cdef int n
    n = floor(a / (2*pi))  # number of times "a" is bigger than 2*pi
    a0 = a - 2*pi * n  # so 0 <= a0 < 2*pi
    return a0 if a0 < pi else a0 - 2*pi
