# -*- coding: utf-8 -*-
import locale
import threading
import re
import string

from datetime import datetime
from contextlib import contextmanager

from itertools import permutations

LOCALE_LOCK = threading.Lock()

@contextmanager
def setlocale(name):
    with LOCALE_LOCK:
        saved = locale.setlocale(locale.LC_ALL)
        try:
            yield locale.setlocale(locale.LC_ALL, name)
        finally:
            locale.setlocale(locale.LC_ALL, saved)


# http://code.activestate.com/recipes/578245-flexible-datetime-parsing/
def str2date(date_string):

    "Parse a date_string into a datetime object."
    date_string = date_string.replace('.', '').replace("/", ' ').replace(",", ' ')
    # The line below remove the accents, which is not good for French
    #date_string = ''.join([c if c in string.printable else ' ' for c in date_string])
    # Dirty hack to fix Free's wrong char in dates
    date_string = date_string.replace('é', 'é')
    date_string = re.sub(r'\s+', ' ', date_string)
    locale_list = ['en_US.UTF-8']
    # Add default locale
    dft_locale = locale.getdefaultlocale()
    if dft_locale and dft_locale[0] and dft_locale[1]:
        dft_locale = '%s.%s' % dft_locale
        if dft_locale not in locale_list:
            locale_list.append(dft_locale)
    for fmt in dateformats():
        for l in locale_list:
            try:
                with setlocale(l):
                    return datetime.strptime(date_string, fmt)
            except ValueError:
                pass

    raise ValueError("'%s' is not a recognized date/time" % date_string)


def dateformats():
    "Yield all combinations of valid date formats."

    years = ["%Y", "%y"]
    months = ["%b", "%B", "%m"]
    days = ["%d"]
    # times = ("%I%p", "%I:%M%p", "%H:%M", "")

    for year in years:
        for month in months:
            for day in days:
                for args in ((day, month), (month, day)):
                    date = " ".join(args)
                    # for time in times:
                    for combo in permutations([year, date]):
                        yield " ".join(combo).strip()
