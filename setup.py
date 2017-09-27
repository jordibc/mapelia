# With this file, one has to run:
#   python3 setup.py build_ext --inplace
# to compile the C module.

from distutils.core import setup

from distutils.extension import Extension
setup(
    ext_modules = [Extension("projections", ["projections.c"])]
)
# The file projections.c is generated from projections.pyx with:
#   cython3 -a projections.pyx
# so we can distribute the code to people that don't have cython installed.
#
# If we don't want to pre-generate projections.c and assume that the end
# user has cython, we could use instead:
#
# from Cython.Build import cythonize
#
# setup(ext_modules = cythonize('projections.pyx'))
#
