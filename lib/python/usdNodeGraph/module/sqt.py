# -*- coding: utf-8 -*-
# __author__ = 'XingHuan'
# 4/16/2018

import os
import sys
from Qt.QtWidgets import *
from Qt.QtCore import *
from Qt.QtGui import *
from Qt import __binding__

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
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import *
    from PyQt5 import QtSvg, QtCharts, QtOpenGL

