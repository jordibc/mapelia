# With this file, one can to run:
#   python3 setup.py develop
# to compile the cython module.

from setuptools import setup

try:
    from Cython.Build import cythonize
except:
    def cythonize(*args, **kwargs):
        return []


setup(
    name='mapelia',
    packages=['mapelia'],
    ext_modules=cythonize(
        ['mapelia/projections.pyx'],
        language_level=3,  # so it compiles for python3 (and not python2)
        compiler_directives={'embedsignature': True}),  # for call signatures
)
