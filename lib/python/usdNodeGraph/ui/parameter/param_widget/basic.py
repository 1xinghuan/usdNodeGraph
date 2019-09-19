from usdNodeGraph.module.sqt import *
from ..parameter import Parameter, Vec3fParameter


class ParameterObject(object):
    parameterClass = None
    parameterValueChanged = Signal()

    @classmethod
    def createParameterWidget(cls, parameter):
        from usdNodeGraph.ui.parameter.register import ParameterRegister

        typeName = parameter.parameterTypeString
        parameterWidgetClass = ParameterRegister.getParameterWidget(typeName)

        if parameterWidgetClass is None:
            print('Un-Support Attribute Type in createParameterWidget! {}'.format(typeName))
            return

        parameterWidget = parameterWidgetClass()
        parameterWidget.setParameter(parameter)

        return parameterWidget

    def __init__(self):
        super(ParameterObject, self).__init__()

        self._parameter = None

    def _breakSignal(self):
        self._parameter.parameterValueChanged.disconnect(self._parameterValueChanged)

    def _reConnectSignal(self):
        self._parameter.parameterValueChanged.connect(self._parameterValueChanged)

    def _parameterValueChanged(self, parameter, value):
        self.updateUI()

    def _setValueFromEdit(self):
        value = self.getPyValue()
        value = self._parameter.convertValueFromPy(value)

        self._breakSignal()

        self._parameter.setValueAt(value)

        self._reConnectSignal()

    def setParameter(self, parameter):
        self._parameter = parameter
        self._reConnectSignal()

        self.updateUI()

    def getParameter(self):
        return self._parameter

    def updateUI(self):
        self.setToolTip(self._parameter.name())

        # todo: timeSamples?
        value = self._parameter.getValue()
        value = self._parameter.convertValueToPy(value)

        self.setPyValue(value)


class ArrayParameterWidget(QWidget, ParameterObject):
    def __init__(self):
        super(ArrayParameterWidget, self).__init__()
        ParameterObject.__init__(self)

        self.masterLayout = QVBoxLayout()
        self.masterLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.masterLayout)

        self.expandButton = QPushButton('expand...')
        self.expandButton.setFixedHeight(20)

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setMinimumHeight(100)
        self.scrollArea.setVisible(0)
        self.areaWidget = None
        self.areaLayout = None

        self.masterLayout.addWidget(self.expandButton)
        self.masterLayout.addWidget(self.scrollArea)

        self.editWidgets = []
        self.lineEdits = []
        self.expanded = 0

        self.expandButton.clicked.connect(self._expandClicked)

    def _getEditWidgetClass(self):
        return None

    def _getChildParamterClass(self):
        return None

    def _expandClicked(self):
        self.expanded = 1 - self.expanded
        if self.areaWidget is None:
            self.areaWidget = QWidget()
            self.areaLayout = QFormLayout()
            self.areaWidget.setLayout(self.areaLayout)
            self.scrollArea.setWidget(self.areaWidget)
        self.scrollArea.setVisible(self.expanded)
        self.expandButton.setFixedHeight(7 if self.expanded else 20)
        self.updateUI()

    def updateUI(self):
        from usdNodeGraph.ui.utils.layout import clearLayout

        self.setToolTip(self._parameter.name())

        if self.areaLayout is not None and self.scrollArea.isVisible():
            clearLayout(self.areaLayout)
            self.editWidgets = []

            # todo: timeSamples?
            value = self._parameter.getValue()
            value = self._parameter.convertValueToPy(value)

            for index, v in enumerate(value):
                editWidgetClass = self._getEditWidgetClass()
                paramClass = self._getChildParamterClass()
                editWidget = editWidgetClass()

                pyValue = paramClass.convertValueToPy(v)
                editWidget.setPyValue(pyValue)

                editWidget.valueChanged.connect(self._editValueChanged)

                self.editWidgets.append(editWidget)
                self.areaLayout.addRow(str(index), editWidget)

    def _editValueChanged(self):
        value = [edit.getPyValue() for edit in self.editWidgets]
        value = self._parameter.convertValueFromPy(value)

        self._breakSignal()

        self._parameter.setValueAt(value)

        self._reConnectSignal()


class LineEdit(QLineEdit):
    def __init__(self):
        super(LineEdit, self).__init__()


class IntLineEdit(LineEdit):
    def __init__(self):
        super(IntLineEdit, self).__init__()

        validator = QIntValidator()
        self.setValidator(validator)


class FloatLineEdit(LineEdit):
    def __init__(self):
        super(FloatLineEdit, self).__init__()

        validator = QDoubleValidator()
        self.setValidator(validator)


class VecWidget(QWidget):
    valueChanged = Signal()
    _valueSize = 1
    _lineEdit = LineEdit

    def __init__(self):
        super(VecWidget, self).__init__()

        self.masterLayout = QHBoxLayout()
        self.masterLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.masterLayout)

        self.lineEdits = []
        for i in range(self._valueSize):
            lineEdit = self._lineEdit()

            # lineEdit.returnPressed.connect(self._editTextChanged)
            lineEdit.editingFinished.connect(self._editTextChanged)

            self.masterLayout.addWidget(lineEdit)
            self.lineEdits.append(lineEdit)

    def _editTextChanged(self):
        self.valueChanged.emit()

    def setPyValue(self, value):
        if not isinstance(value, list):
            value = [value]
        for index, v in enumerate(value):
            lineEdit = self.lineEdits[index]
            lineEdit.setText(str(v))

    def getPyValue(self):
        value = [float(edit.text()) for edit in self.lineEdits]
        if len(value) == 1:
            value = value[0]
        return value

