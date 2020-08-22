# -*- coding: utf-8 -*-
from usdNodeGraph.module.sqt import QtWidgets, QtGui, QtCore


LOG_WINDOW = None
RED_COLOR = QtGui.QColor(221, 30, 30)


class LogWindow(QtWidgets.QWidget):
    def __init__(self):
        super(LogWindow, self).__init__()

        global LOG_WINDOW
        LOG_WINDOW = self

        self.masterLayout = QtWidgets.QVBoxLayout()
        self.setLayout(self.masterLayout)

        self.textEdit = QtWidgets.QTextEdit()
        self.stdoutTextFormat = QtGui.QTextCharFormat()
        self.defaultTextColor = self.textEdit.palette().color(self.textEdit.foregroundRole())
        self.stdoutTextFormat.setForeground(self.defaultTextColor)

        self.masterLayout.addWidget(self.textEdit)

    def showMessage(self, message, mode='DEBUG'):
        message += '\n'
        if mode.startswith('DEBUG'):
            self.stdoutTextFormat.setForeground(QtGui.QColor(85, 170, 85))
        elif mode.startswith('INFO'):
            self.stdoutTextFormat.setForeground(QtGui.QColor(119, 221, 119))
        elif mode.startswith('WARNING'):
            self.stdoutTextFormat.setForeground(RED_COLOR)
        elif mode.startswith('ERROR'):
            self.stdoutTextFormat.setForeground(RED_COLOR)
        else:
            self.stdoutTextFormat.setForeground(self.defaultTextColor)
        self.textEdit.moveCursor(QtGui.QTextCursor.End)
        self.textEdit.textCursor().insertText(message, self.stdoutTextFormat)

    @classmethod
    def debug(cls, message):
        logWindow = getLogWindow()
        logWindow.showMessage(message, 'DEBUG')

    @classmethod
    def warning(cls, message):
        logWindow = getLogWindow()
        logWindow.show()
        logWindow.showMessage(message, 'WARNING')

    @classmethod
    def error(cls, message):
        logWindow = getLogWindow()
        logWindow.show()
        logWindow.showMessage(message, 'ERROR')


def getLogWindow():
    if not LOG_WINDOW:
        logWindow = LogWindow()
    return LOG_WINDOW


