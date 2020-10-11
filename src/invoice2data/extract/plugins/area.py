"""
Plugin to extract tables from an invoice.
"""

import logging
import re
import subprocess
from distutils import spawn  # py2 compat

logger = logging.getLogger(__name__)

DEFAULT_OPTIONS = {'field_separator': r'\s+', 'line_separator': r'\n'}


def extract(self, content, path, output):
    """Try to extract values using area from an invoice"""

    for area in self['area']:

        # First apply default options.
        plugin_settings = DEFAULT_OPTIONS.copy()
        plugin_settings.update(area)
        area = plugin_settings

        # Validate settings
        assert 'name' in area, 'Area name  missing'
        assert 'area' in area, 'Area area details missing'
        assert 'r' in area["area"], 'Area R details missing'
        assert 'x' in area["area"], 'Area X details missing'
        assert 'y' in area["area"], 'Area y details missing'
        assert 'W' in area["area"], 'Area W details missing'
        assert 'H' in area["area"], 'Area H details missing'
        r = str(area['area']["r"])
        x = str(area['area']["x"])
        y = str(area['area']["y"])
        W = str(area['area']["W"])
        H = str(area['area']["H"])
        if spawn.find_executable("pdftotext"):  # shutil.which('pdftotext'):
            out, err = subprocess.Popen(
                ["pdftotext","-layout", "-enc", "UTF-8",'-r',r,'-x',x,'-y',y,'-W',W,'-H',H, path, '-'],
                stdout=subprocess.PIPE


            ).communicate()
            if 'regex' in area:
                reg_string = re.search(area["regex"], out.decode("utf-8"))
                output[area["name"]] = reg_string.group()
            else:
                output[area["name"]] = out.decode("utf-8")
        else:
            raise EnvironmentError(
                'pdftotext not installed. Can be downloaded from https://poppler.freedesktop.org/'
            )



            # logger.debug('ignoring *%s* because it doesn\'t match anything', line)
