from .basic import ParameterObject
from usdNodePraph.module.sqt import *
from ..parameter import Parameter, StringParameter, FilePathParameter, TextParameter


class StringWidget(QWidget):
    valueChanged = Signal()

    def __init__(self):
        super(StringWidget, self).__init__()

        self.masterLayout = QHBoxLayout()
        self.masterLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.masterLayout)

        self._lineEdit = QLineEdit()
        self.masterLayout.addWidget(self._lineEdit)

        self._lineEdit.returnPressed.connect(self._editTextChanged)

    def _editTextChanged(self):
        self.valueChanged.emit()

    def setPyValue(self, value):
        self._lineEdit.setText(str(value))

    def getPyValue(self):
        return str(self._lineEdit.text())


class StringParameterWidget(StringWidget, ParameterObject):
    def __init__(self):
        ParameterObject.__init__(self)
        super(StringParameterWidget, self).__init__()

    def _editTextChanged(self):
        super(StringParameterWidget, self)._editTextChanged()

        self._setValueFromEdit()


class ChooseWidget(QWidget):
    valueChanged = Signal()

    def __init__(self):
        super(ChooseWidget, self).__init__()

        self.masterLayout = QHBoxLayout()
        self.masterLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.masterLayout)

        self._comboBox = QComboBox()
        self.masterLayout.addWidget(self._comboBox)

        self._comboBox.currentIndexChanged.connect(self._editIndexChanged)

    def _editIndexChanged(self):
        self.valueChanged.emit()

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


class ChooseParameterWidget(ChooseWidget, ParameterObject):
    def __init__(self):
        ParameterObject.__init__(self)
        super(ChooseParameterWidget, self).__init__()

    def setParameter(self, parameter):
        super(ChooseParameterWidget, self).setParameter(parameter)

        for value in self.getParameter().getItems():
            if self._comboBox.findText(value) == -1:
                self._comboBox.addItem(value)

    def _editIndexChanged(self):
        super(ChooseParameterWidget, self)._editIndexChanged()

        self._setValueFromEdit()


class TextWidget(QTextEdit):
    valueChanged = Signal()

    def __init__(self):
        super(TextWidget, self).__init__()

        self.setMinimumWidth(200)

        self.textChanged.connect(self._editTextChanged)

    def _editTextChanged(self):
        self.valueChanged.emit()

    def setPyValue(self, value):
        self.setPlainText(value)

    def getPyValue(self):
        return str(self.toPlainText())


class TextParameterWidget(TextWidget, ParameterObject):
    def __init__(self):
        ParameterObject.__init__(self)
        super(TextParameterWidget, self).__init__()

    def _editTextChanged(self):
        super(TextParameterWidget, self)._editTextChanged()

        self._setValueFromEdit()



