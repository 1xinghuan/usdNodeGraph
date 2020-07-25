
import os
from usdNodeGraph.module.sqt import *
from usdNodeGraph.utils.res import resource


TEXT_COLOR = QtGui.QColor(220, 220, 220)
DISABLED_COLOR = QtGui.QColor(150, 150, 150)


class DarkPalette(QtGui.QPalette):
    def __init__(self):
        super(DarkPalette, self).__init__()

        self.setColor(QtGui.QPalette.Window, QtGui.QColor(50, 50, 50))
        self.setColor(QtGui.QPalette.WindowText, TEXT_COLOR)
        self.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.WindowText, DISABLED_COLOR)

        self.setColor(QtGui.QPalette.Text, TEXT_COLOR)
        self.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Text, DISABLED_COLOR)

        self.setColor(QtGui.QPalette.ToolTipBase, TEXT_COLOR)
        self.setColor(QtGui.QPalette.ToolTipText, QtGui.QColor(50, 50, 50))

        self.setColor(QtGui.QPalette.Base, QtGui.QColor(40, 40, 40))
        self.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(60, 60, 60))

        self.setColor(QtGui.QPalette.Dark, QtGui.QColor(30, 30, 30))
        self.setColor(QtGui.QPalette.Shadow, QtGui.QColor(20, 20, 20))

        self.setColor(QtGui.QPalette.Button, QtGui.QColor(50, 50, 50))
        self.setColor(QtGui.QPalette.ButtonText, TEXT_COLOR)
        self.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, DISABLED_COLOR)

        self.setColor(QtGui.QPalette.BrightText, QtGui.QColor(200, 20, 20))
        self.setColor(QtGui.QPalette.Link, QtGui.QColor(40, 120, 200))

        self.setColor(QtGui.QPalette.Highlight, QtGui.QColor(40, 130, 200))
        self.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Highlight, QtGui.QColor(120, 120, 120))

        self.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(40, 200, 200))
        self.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.HighlightedText, QtGui.QColor(120, 120, 120))


class MainApplication(QtWidgets.QApplication):
    def __init__(self, *args, **kwargs):
        super(MainApplication, self).__init__(*args, **kwargs)

        darkPalette = DarkPalette()
        self.setPalette(darkPalette)

        guiStyle = resource.get_style('style')
        self.setStyleSheet(guiStyle)



