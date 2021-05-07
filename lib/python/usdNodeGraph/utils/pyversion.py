import sys

PY_MAIN_VERSION = sys.version_info[0]

if PY_MAIN_VERSION == 3:
    from imp import reload
    basestring = str
    unicode = str
    long = int
else:
    reload = reload
    basestring = basestring

