"""
Convierte ficheros asc en ficheros ply.
"""

from numpy import sqrt, arcsin, arctan2, floor, pi


def get_points_raw(fname):
    "Return a list of points from an asc file"
    points_raw = []
    for line in open(fname):
        if line.strip():
            points_raw.append([float(num) for num in line.split()[:3]])
    return points_raw


def get_points(points_raw, row_length=0):
    "Return points (list of rows) from a list of raw points"
    fast_angle = find_fast_angle(points_raw)

    points = []
    row = []
    pid = 0
    delta_threshold = 0.001 * pi / sqrt(len(points_raw))
    for x, y, z in points_raw:
        r = sqrt(x**2 + y**2 + z**2)
        theta = arctan2(y, x)
        phi = arcsin(z / r)

        # See if we have to add a new row.
        if pid == 0:
            pass
        elif row_length > 0:
            if pid % row_length == 0:
                points.append(row)
                row = []
        else:
            d_theta = mod(theta - theta_last, 2 * pi)
            d_phi = mod(phi - phi_last, pi)
            if fast_angle == 'theta':
                if abs(d_phi) > delta_threshold:
                    points.append(row)
                    row = []
            elif fast_angle == 'phi':
                if abs(d_theta) > delta_threshold:
                    points.append(row)
                    row = []

        row.append([pid, x, y, z])
        theta_last, phi_last = theta, phi
        pid += 1
    points.append(row)  # don't forget to append the last row!
    return points


def find_fast_angle(points_raw):
    "Return the angle that changes faster between consecutive points"
    d_thetas, d_phis = [], []
    pid = 0
    for x, y, z in points_raw:
        r = sqrt(x**2 + y**2 + z**2)
        theta = arctan2(y, x)
        phi = arcsin(z / r)
        if pid > 0:
            d_thetas.append(abs(mod(theta - theta_last, 2 * pi)))
            d_phis.append(abs(mod(phi - phi_last, pi)))
        theta_last, phi_last = theta, phi
        pid += 1
        if pid > 10:  # enough to get an idea
            break
    return 'theta' if sum(d_thetas) > sum(d_phis) else 'phi'


def mod(x, y):
    "Return the representative of x between -y/2 and y/2 for the group R/yR"
    x0 = x - y * floor(x / y)
    return x0 if x0 < y / 2 else x0 - y
