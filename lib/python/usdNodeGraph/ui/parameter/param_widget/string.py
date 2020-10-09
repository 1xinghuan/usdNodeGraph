from .basic import ParameterWidget, VecWidget
from usdNodeGraph.module.sqt import *


class StringParameterWidget(VecWidget, ParameterWidget):
    def __init__(self):
        super(StringParameterWidget, self).__init__()
        ParameterWidget.__init__(self)


class ChooseWidget(QtWidgets.QWidget):
    editValueChanged = QtCore.Signal()

    def __init__(self):
        super(ChooseWidget, self).__init__()

        self.masterLayout = QtWidgets.QHBoxLayout()
        self.masterLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.masterLayout)

        self._comboBox = QtWidgets.QComboBox()
        self._comboBox.setEditable(True)
        self.masterLayout.addWidget(self._comboBox)

        self._comboBox.currentIndexChanged.connect(self._editIndexChanged)

    def _editIndexChanged(self):
        self.editValueChanged.emit()

    def _setMasterWidgetEnable(self, enable):
        self._comboBox.setVisible(enable)

    def setPyValue(self, value):
        index = self._comboBox.findText(value)
        if index != -1:
            self._comboBox.setCurrentIndex(index)
        else:
            # not exist
            self._comboBox.addItem(value)
            self._comboBox.setCurrentIndex(self._comboBox.count() - 1)

    def getPyValue(self):
        return str(self._comboBox.currentText())


class ChooseParameterWidget(ChooseWidget, ParameterWidget):
    def __init__(self):
        super(ChooseParameterWidget, self).__init__()
        ParameterWidget.__init__(self)

    def setParameter(self, parameter):
        super(ChooseParameterWidget, self).setParameter(parameter)
        self._beforeUpdateUI()
        for value in self.getParameter().getItems():
            if self._comboBox.findText(value) == -1:
                self._comboBox.addItem(value)
        self._afterUpdateUI()


class TextWidget(QtWidgets.QTextEdit):
    editValueChanged = QtCore.Signal()

    def __init__(self):
        super(TextWidget, self).__init__()

        # self.setMinimumWidth(200)

        self.textChanged.connect(self._editTextChanged)

    def _editTextChanged(self):
        self.editValueChanged.emit()

    def setPyValue(self, value):
        self.setPlainText(value)

    def getPyValue(self):
        return str(self.toPlainText())


class TextParameterWidget(TextWidget, ParameterWidget):
    def __init__(self):
        super(TextParameterWidget, self).__init__()
        ParameterWidget.__init__(self)


