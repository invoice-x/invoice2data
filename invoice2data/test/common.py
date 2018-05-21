import os
import pkg_resources
import logging

# Reduce log level of various modules
logging.getLogger('chardet').setLevel(logging.WARNING)
logging.getLogger('pdfminer').setLevel(logging.WARNING)


def get_sample_files(extension):
    compare_files = []
    for path, subdirs, files in os.walk(pkg_resources.resource_filename(__name__, 'compare')):
        for file in files:
            if file.endswith(extension):
                compare_files.append(os.path.join(path, file))
    return compare_files