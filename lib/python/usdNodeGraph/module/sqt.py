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
if __binding__ == 'PySide2':
    try:
        from PySide2.QtCharts import QtCharts
        use_qtcharts = True
    except:
        pass


# for pycharm auto complete
if False:
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import *
    from PyQt5 import QtSvg, QtCharts

