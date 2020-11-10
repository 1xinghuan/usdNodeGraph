from .basic import ParameterWidget, VecWidget, VecParameterWidget
from usdNodeGraph.module.sqt import *


class StringParameterWidget(VecWidget, VecParameterWidget):
    def __init__(self):
        super(StringParameterWidget, self).__init__()
        ParameterWidget.__init__(self)


class ChooseWidget(QtWidgets.QWidget):
    editValueChanged = QtCore.Signal()

    def __init__(self):
        super(ChooseWidget, self).__init__()

        self._options = []
        self._map = {}

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

    def addOption(self, option):
        if isinstance(option, basestring):
            label = option
            value = option
        else:
            label, value = option
        self._options.append(label)
        self._map.update({value: label})
        return label

    def setPyValue(self, value):
        valueString = str(value)
        if valueString in self._map:
            label = self._map.get(valueString)
            index = self._comboBox.findText(label)
            self._comboBox.setCurrentIndex(index)
        else:
            # not exist
            self.addOption(valueString)
            self._comboBox.addItem(valueString)
            self._comboBox.setCurrentIndex(self._comboBox.count() - 1)

    def getPyValue(self):
        label = str(self._comboBox.currentText())
        for k, v in self._map.items():
            if k == label:
                return v


class ChooseParameterWidget(ChooseWidget, ParameterWidget):
    def __init__(self):
        super(ChooseParameterWidget, self).__init__()
        ParameterWidget.__init__(self)

    def setParameter(self, parameter):
        super(ChooseParameterWidget, self).setParameter(parameter)
        self._beforeUpdateUI()
        for option in self.getParameter().getHintValue('options', defaultValue=[]):
            label = self.addOption(option)
            if self._comboBox.findText(label) == -1:
                self._comboBox.addItem(label)
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


