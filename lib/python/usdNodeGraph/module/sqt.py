# -*- coding: utf-8 -*-
# __author__ = 'XingHuan'
# 4/16/2018

import os

if os.environ.get('QT_PREFERRED_BINDING') == 'PyQt4':
    os.environ['QT_PREFERRED_BINDING'] = 'PySide'
elif os.environ.get('QT_PREFERRED_BINDING') == 'PyQt5':
    os.environ['QT_PREFERRED_BINDING'] = 'PySide2'

from Qt.QtWidgets import *
from Qt.QtCore import *
from Qt.QtGui import *
from Qt import QtCompat, QtSvg, __binding__

print('usdNodeGraph using qt binding: {}'.format(__binding__))

use_qtcharts = False
if __binding__ == 'PyQt5':
    try:
        import PyQt5.QtChart as QtCharts
        use_qtcharts = True
    except:
        pass
elif __binding__ == 'PySide2':
    try:
        from PySide2.QtCharts import QtCharts
        use_qtcharts = True
    except:
        pass


def loadUI(uifile, parent):
    QtCompat.loadUi(uifile=uifile, baseinstance=parent)


def to_unicode(qstring):
    from sins import PYTHON_MAIN_VERSION
    if PYTHON_MAIN_VERSION == 2:
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


def to_date(qdate):
    try:
        date_value = qdate.toPyDate()
    except AttributeError:  # in PySide, use toPython()
        date_value = qdate.toPython()
    return date_value


# for pycharm auto complete
if False:
    from PyQt4.QtCore import *
    from PyQt4.QtGui import *
    from PyQt4.QtWidgets import *
    from PyQt5 import QtSvg, QtCharts

