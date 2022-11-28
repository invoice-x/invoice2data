# -*- coding: utf-8 -*-
def to_text(path: str, area_details: dict = None):
    """Wrapper around Poppler pdftotext.

    Parameters
    ----------
    path : str
        path of electronic invoice in PDF
    area_details : dictionary
        of the format {x: int, y: int, r: int, W: int, H: int}
        used when extracting an area of the pdf rather than the whole document

    Returns
    -------
    out : str
        returns extracted text from pdf

    Raises
    ------
    EnvironmentError:
        If pdftotext library is not found
    """
    import subprocess
    from distutils import spawn  # py2 compat

    if spawn.find_executable("pdftotext"):  # shutil.which('pdftotext'):
        cmd = ["pdftotext", "-layout", "-enc", "UTF-8"]
        if area_details is not None:
            # An area was specified
            # Validate the required keys were provided
            assert 'f' in area_details, 'Area r details missing'
            assert 'l' in area_details, 'Area r details missing'
            assert 'r' in area_details, 'Area r details missing'
            assert 'x' in area_details, 'Area x details missing'
            assert 'y' in area_details, 'Area y details missing'
            assert 'W' in area_details, 'Area W details missing'
            assert 'H' in area_details, 'Area H details missing'
            # Convert all of the values to strings
            for key in area_details.keys():
                area_details[key] = str(area_details[key])
            cmd += [
                '-f', area_details['f'],
                '-l', area_details['l'],
                '-r', area_details['r'],
                '-x', area_details['x'],
                '-y', area_details['y'],
                '-W', area_details['W'],
                '-H', area_details['H'],
            ]
        cmd += [path, "-"]
        # Run the extraction
        out, err = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()
        return out
    else:
        raise EnvironmentError(
            "pdftotext not installed. Can be downloaded from https://poppler.freedesktop.org/"
        )
