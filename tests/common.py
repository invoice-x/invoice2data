import os
import pkg_resources
import logging

# Reduce log level of various modules
logging.getLogger('pdfminer').setLevel(logging.WARNING)


def get_sample_files(extension, exclude_input_specific=True):
    compare_files = []
    for path, subdirs, files in os.walk(pkg_resources.resource_filename(__name__, 'compare')):
        for file in files:
            # exclude files which need an specific input module
            if exclude_input_specific and inputparser_specific(file):
                continue
            if file.endswith(extension):
                compare_files.append(os.path.join(path, file))
    return compare_files


def exclude_template(test_list, exclude_list):
    for elem in test_list[:]:
        for end in exclude_list:
            if elem.endswith(end):
                test_list.remove(elem)
    return test_list


def inputparser_specific(file):
    if file.startswith("saeco"):
        return True
