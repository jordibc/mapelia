# This file exists so we can create simple executables with
# pyproject.toml in the [project.scripts] section.
#
# And at the same time we can use the files directly like executables,
# for example with ./pintelia.py ...

import sys
import os

sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from .mapelia import main as main_mapelia
from .pintelia import main as main_pintelia
from .poligoniza import main as main_poligoniza
from .stl_split import main as main_stl_split
from .smooth import main as main_smooth

try:
    from .guapelia import main as main_guapelia
except ModuleNotFoundError as e:  # this can be common
    def main_guapelia():
        print('Cannot use gtk. Maybe try: pip install pygobject')
