# -*- coding: utf-8 -*-

from usdNodeGraph.module.sqt import QtWidgets, QtGui, QtCore
import math


EDIT_LABEL_HEIGHT = 40
EDIT_LABEL_WIDTH = 70


class NumberEditLabel(QtWidgets.QLabel):
    def __init__(self, sample=1, *args, **kwargs):
        super(NumberEditLabel, self).__init__(*args, **kwargs)

        self.sample = sample
        self.currentValue = 0

        self.setText(str(sample))
        self.setFixedSize(EDIT_LABEL_WIDTH, EDIT_LABEL_HEIGHT)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setStyleSheet("""
        background: rgb(40, 40, 40)
        """)

    def addValue(self, value):
        self.currentValue += value
        self.setText('+{}'.format(self.currentValue) if self.currentValue > 0 else str(self.currentValue))

    def setDefault(self):
        self.currentValue = 0
        self.setText(str(self.sample))

    def setEditing(self, editing):
        if editing:
            self.setStyleSheet("""
            border: 1px solid rgb(120, 120, 120);
            background: rgb(40, 40, 40)
            """)
        else:
            self.setDefault()
            self.setStyleSheet("""
            background: rgb(40, 40, 40)
            """)


class _NumberEditWidget(QtWidgets.QWidget):
    numberSamples = [100, 10, 1, 0.1, 0.01, 0.001, 0.0001]
    def __init__(self, *args, **kwargs):
        super(_NumberEditWidget, self).__init__(*args, **kwargs)

        self.editLabels = []
        self.currentEditLabel = None

        self.initUI()

    def initUI(self):
        self.masterLayout = QtWidgets.QVBoxLayout()
        self.masterLayout.setContentsMargins(0, 0, 0, 0)
        self.masterLayout.setSpacing(0)
        self.setLayout(self.masterLayout)

        for i in self.numberSamples:
            editLabel = NumberEditLabel(i, parent=self)
            self.masterLayout.addWidget(editLabel)
            self.editLabels.append(editLabel)

        self.setFixedSize(EDIT_LABEL_WIDTH, EDIT_LABEL_HEIGHT * len(self.numberSamples))

    def setEditingPos(self, pos):
        y = self.height() / 2 + pos.y()
        editIndex = int(math.floor(float(y) / EDIT_LABEL_HEIGHT))
        editIndex = max(editIndex, 0)
        editIndex = min(editIndex, len(self.editLabels))
        if self.currentEditLabel is not None and self.currentEditLabel != self.editLabels[editIndex]:
            self.currentEditLabel.setEditing(False)
        self.editLabels[editIndex].setEditing(True)
        self.currentEditLabel = self.editLabels[editIndex]

        x = pos.x()
        value = x * self.currentEditLabel.sample
        self.currentEditLabel.addValue(value)

        return value


class IntEditWidget(_NumberEditWidget):
    numberSamples = [100, 10, 1]


class FloatEditWidget(_NumberEditWidget):
    pass
