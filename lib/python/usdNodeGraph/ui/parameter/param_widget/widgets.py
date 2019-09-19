from usdNodeGraph.module.sqt import *
from .basic import *
from ..parameter import *
from .string import *


class BoolWidget(QWidget):
    valueChanged = Signal()

    def __init__(self):
        super(BoolWidget, self).__init__()

        self.masterLayout = QHBoxLayout()
        self.masterLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.masterLayout)

        self.checkBox = QCheckBox()
        self.masterLayout.addWidget(self.checkBox)

        self.checkBox.stateChanged.connect(self._checkedChanged)

    def _checkedChanged(self):
        self.valueChanged.emit()

    def setPyValue(self, value):
        self.checkBox.setChecked(value)

    def getPyValue(self):
        return self.checkBox.isChecked()


class BoolParameterWidget(BoolWidget, ParameterObject):
    def __init__(self):
        ParameterObject.__init__(self)
        super(BoolParameterWidget, self).__init__()

    def _checkedChanged(self):
        super(BoolParameterWidget, self)._checkedChanged()

        self._setValueFromEdit()


class IntWidget(VecWidget):
    _valueSize = 1
    _lineEdit = IntLineEdit


class IntParameterWidget(IntWidget, ParameterObject):
    def __init__(self):
        ParameterObject.__init__(self)
        super(IntParameterWidget, self).__init__()

    def _editTextChanged(self):
        super(IntParameterWidget, self)._editTextChanged()

        self._setValueFromEdit()


class FloatWidget(VecWidget):
    _valueSize = 1
    _lineEdit = FloatLineEdit


class FloatParameterWidget(FloatWidget, ParameterObject):
    def __init__(self):
        ParameterObject.__init__(self)
        super(FloatParameterWidget, self).__init__()

    def _editTextChanged(self):
        super(FloatParameterWidget, self)._editTextChanged()

        self._setValueFromEdit()


class Vec2fWidget(FloatWidget):
    _valueSize = 2


class Vec2fParameterWidget(Vec2fWidget, ParameterObject):
    def __init__(self):
        ParameterObject.__init__(self)
        super(Vec2fParameterWidget, self).__init__()

    def _editTextChanged(self):
        super(Vec2fParameterWidget, self)._editTextChanged()

        self._setValueFromEdit()


class Vec3fWidget(FloatWidget):
    _valueSize = 3


class Vec3fParameterWidget(Vec3fWidget, ParameterObject):
    def __init__(self):
        ParameterObject.__init__(self)
        super(Vec3fParameterWidget, self).__init__()

    def _editTextChanged(self):
        super(Vec3fParameterWidget, self)._editTextChanged()

        self._setValueFromEdit()


class Vec4fWidget(FloatWidget):
    _valueSize = 4


class Vec4fParameterWidget(Vec4fWidget, ParameterObject):
    def __init__(self):
        ParameterObject.__init__(self)
        super(Vec4fParameterWidget, self).__init__()

    def _editTextChanged(self):
        super(Vec4fParameterWidget, self)._editTextChanged()

        self._setValueFromEdit()


