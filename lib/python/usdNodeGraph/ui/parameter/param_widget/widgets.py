from .basic import *
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
        super(BoolParameterWidget, self).__init__()
        ParameterWidget.__init__(self)


class IntWidget(VecWidget):
    _valueSize = 1
    _lineEdit = IntLineEdit


class IntParameterWidget(IntWidget, VecParameterWidget):
    def __init__(self):
        super(IntParameterWidget, self).__init__()
        VecParameterWidget.__init__(self)


class FloatWidget(VecWidget):
    _valueSize = 1
    _lineEdit = FloatLineEdit


class FloatParameterWidget(FloatWidget, VecParameterWidget):
    def __init__(self):
        super(FloatParameterWidget, self).__init__()
        VecParameterWidget.__init__(self)


class Vec2fWidget(FloatWidget):
    _valueSize = 2


class Vec2fParameterWidget(Vec2fWidget, VecParameterWidget):
    def __init__(self):
        super(Vec2fParameterWidget, self).__init__()
        VecParameterWidget.__init__(self)


class Vec3fWidget(FloatWidget):
    _valueSize = 3


class Vec3fParameterWidget(Vec3fWidget, VecParameterWidget):
    def __init__(self):
        super(Vec3fParameterWidget, self).__init__()
        VecParameterWidget.__init__(self)


class Vec4fWidget(FloatWidget):
    _valueSize = 4


class Vec4fParameterWidget(Vec4fWidget, VecParameterWidget):
    def __init__(self):
        super(Vec4fParameterWidget, self).__init__()
        VecParameterWidget.__init__(self)


class Matrix2dWidget(MatrixWidget):
    _valueSize = 2


class Matrix2dParameterWidget(Matrix2dWidget, VecParameterWidget):
    def __init__(self):
        super(Matrix2dParameterWidget, self).__init__()
        VecParameterWidget.__init__(self)


class Matrix3dWidget(MatrixWidget):
    _valueSize = 3


class Matrix3dParameterWidget(Matrix3dWidget, VecParameterWidget):
    def __init__(self):
        super(Matrix3dParameterWidget, self).__init__()
        VecParameterWidget.__init__(self)


class Matrix4dWidget(MatrixWidget):
    _valueSize = 4


class Matrix4dParameterWidget(Matrix4dWidget, VecParameterWidget):
    def __init__(self):
        super(Matrix4dParameterWidget, self).__init__()
        VecParameterWidget.__init__(self)

