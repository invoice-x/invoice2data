# -*- coding: utf-8 -*-


def to_text(path):
    """Wraps Tesseract OCR.

    Parameters
    ----------
    path : str
        path of electronic invoice in JPG or PNG format

    Returns
    -------
    extracted_str : str
        returns extracted text from image in JPG or PNG format

    """
    import subprocess
    from distutils import spawn
    from pdf2image import convert_from_path
    from PIL import Image



    # Check for dependencies. Needs Tesseract and Imagemagick installed.
    if not spawn.find_executable('tesseract'):
        raise EnvironmentError('tesseract not installed.')
    if not spawn.find_executable('convert'):
        raise EnvironmentError('imagemagick not installed.')

    pages = convert_from_path(path, 500)
    if(len(pages)==1):
        pages[0].save('out.jpg', 'JPEG')
    else:
        imagefiles = []
        i = 0
        for page in pages:
            page.save('out'+str(i)+'.jpg', 'JPEG')
            imagefiles.append('out'+str(i)+'.jpg')
        images = map(Image.open, imagefiles)
        widths, heights = zip(*(i.size for i in images))
        total_width = sum(widths)
        max_height = max(heights)
        new_im = Image.new('RGB', (total_width, max_height))
        x_offset = 0
        for im in images:
            new_im.paste(im, (x_offset,0))
            x_offset += im.size[0]
        new_im.save('out.jpg')


    # convert = "convert -density 350 %s -depth 8 tiff:-" % (path)
    convert = ['convert', '-density', '350', 'out.jpg', '-depth', '8', 'JPG:-']
    p1 = subprocess.Popen(convert, stdout=subprocess.PIPE, shell=True)

    tess = ['tesseract', 'stdin', 'stdout']
    p2 = subprocess.Popen(tess, stdin=p1.stdout, stdout=subprocess.PIPE)

    out, err = p2.communicate()

    extracted_str = out

    return extracted_str
