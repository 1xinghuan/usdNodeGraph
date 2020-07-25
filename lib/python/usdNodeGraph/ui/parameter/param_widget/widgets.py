from usdNodeGraph.module.sqt import *
from .basic import *
from ..parameter import *
from .string import *


class BoolWidget(QtWidgets.QWidget):
    editValueChanged = QtCore.Signal()

    def __init__(self):
        super(BoolWidget, self).__init__()

        self.masterLayout = QtWidgets.QHBoxLayout()
        self.masterLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.masterLayout)

        self.checkBox = QtWidgets.QCheckBox()
        self.masterLayout.addWidget(self.checkBox)

        self.checkBox.stateChanged.connect(self._checkedChanged)

    def _checkedChanged(self):
        self.editValueChanged.emit()

    def _setMasterWidgetEnable(self, enable):
        self.checkBox.setVisible(enable)

    def setPyValue(self, value):
        self.checkBox.setChecked(value)

    def getPyValue(self):
        return self.checkBox.isChecked()


class BoolParameterWidget(BoolWidget, ParameterWidget):
    def __init__(self):
        ParameterWidget.__init__(self)
        super(BoolParameterWidget, self).__init__()

    def _checkedChanged(self):
        super(BoolParameterWidget, self)._checkedChanged()

        self._setValueFromEdit()


class IntWidget(VecWidget):
    _valueSize = 1
    _lineEdit = IntLineEdit


class IntParameterWidget(IntWidget, ParameterWidget):
    def __init__(self):
        ParameterWidget.__init__(self)
        super(IntParameterWidget, self).__init__()

    def _editTextChanged(self):
        super(IntParameterWidget, self)._editTextChanged()

        self._setValueFromEdit()


class FloatWidget(VecWidget):
    _valueSize = 1
    _lineEdit = FloatLineEdit


class FloatParameterWidget(FloatWidget, ParameterWidget):
    def __init__(self):
        ParameterWidget.__init__(self)
        super(FloatParameterWidget, self).__init__()

    def _editTextChanged(self):
        super(FloatParameterWidget, self)._editTextChanged()

        self._setValueFromEdit()


class Vec2fWidget(FloatWidget):
    _valueSize = 2


class Vec2fParameterWidget(Vec2fWidget, ParameterWidget):
    def __init__(self):
        ParameterWidget.__init__(self)
        super(Vec2fParameterWidget, self).__init__()

    def _editTextChanged(self):
        super(Vec2fParameterWidget, self)._editTextChanged()

        self._setValueFromEdit()


class Vec3fWidget(FloatWidget):
    _valueSize = 3


class Vec3fParameterWidget(Vec3fWidget, ParameterWidget):
    def __init__(self):
        ParameterWidget.__init__(self)
        super(Vec3fParameterWidget, self).__init__()

    def _editTextChanged(self):
        super(Vec3fParameterWidget, self)._editTextChanged()

        self._setValueFromEdit()


class Vec4fWidget(FloatWidget):
    _valueSize = 4


class Vec4fParameterWidget(Vec4fWidget, ParameterWidget):
    def __init__(self):
        ParameterWidget.__init__(self)
        super(Vec4fParameterWidget, self).__init__()

    def _editTextChanged(self):
        super(Vec4fParameterWidget, self)._editTextChanged()

        self._setValueFromEdit()


