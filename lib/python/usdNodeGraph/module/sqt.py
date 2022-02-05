# -*- coding: utf-8 -*-

import os
import sys

from Qt import __binding__, QtWidgets, QtCore, QtGui

# QtCore.Signal = QtCore.pyqtSignal

PY_MAIN_VERSION = sys.version_info[0]

print('usdNodeGraph using qt binding: {}'.format(__binding__))


def to_unicode(qstring):
    if PY_MAIN_VERSION == 2:
        if isinstance(qstring, unicode):
            return qstring
        elif isinstance(qstring, str):
            return unicode(qstring, 'utf-8')
        else:
            try:
                return unicode(qstring.toUtf8(), 'utf-8')  # PyQt4
            except:
                return ''
    else:
        # qstring not exist in python 3
        return qstring


# for pycharm auto complete
if False:
    from PySide2 import QtSvg, QtCharts, QtOpenGL, QtWidgets, QtCore, QtGui

