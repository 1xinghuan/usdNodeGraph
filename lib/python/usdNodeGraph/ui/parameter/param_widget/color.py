from .widgets import *


class ColorButton(QtWidgets.QLabel):
    colorChanged = QtCore.Signal()

    def __init__(self):
        super(ColorButton, self).__init__()

        self._color = (0, 0, 0, 255)

        self.setFixedSize(20, 20)
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def updateColor(self):
        if self._color is None:
            return

        colorString = 'rgba(%s, %s, %s, %s)' % self._color
        self.setStyleSheet("""
        QLabel{
            background: %s;
            border: 1px solid gray;
        }
        """ % colorString)
        self.setToolTip(colorString)

    def _get255Color(self, floatColor):
        return max(min(floatColor * 255.0, 255.0), 0)

    def setColor(self, color):
        if color is None:
            pass
        elif len(color) == 3:
            self._color = (self._get255Color(color[0]), self._get255Color(color[1]), self._get255Color(color[2]), 255)
        elif len(color) == 4:
            self._color = (self._get255Color(color[0]), self._get255Color(color[1]), self._get255Color(color[2]), self._get255Color(color[3]))
        self.updateColor()

    def getColor(self):
        return self._color

    def getFloatColor(self):
        return [i / 255.0 for i in self._color]

    def mouseReleaseEvent(self, QMouseEvent):
        super(ColorButton, self).mouseReleaseEvent(QMouseEvent)

        window = QtWidgets.QColorDialog()
        window.setCurrentColor(QtGui.QColor(*self._color))
        result = window.exec_()
        if result:
            color = window.selectedColor()
            self._color = (color.red(), color.green(), color.blue(), color.alpha())
            self.colorChanged.emit()

class ColorWidget(FloatWidget):
    def initUI(self):
        super(ColorWidget, self).initUI()

        self.colorLabel = ColorButton()
        self.masterLayout.insertWidget(0, self.colorLabel)

        self.colorLabel.colorChanged.connect(self._colorLabelChanged)

    def setPyValue(self, value):
        super(ColorWidget, self).setPyValue(value)
        self.colorLabel.setColor(value)

    def _colorLabelChanged(self):
        color = self.getParameter().convertValueFromPy(self.colorLabel.getFloatColor())
        self.getParameter().setValue(color)


class ColorParameterWidget(VecParameterWidget):
    def setParameter(self, parameter, update=False):
        super(ColorParameterWidget, self).setParameter(parameter, update)
        self.setEditorsVisible(parameter.getHintValue('showEditor', True))

    def _setMasterWidgetEnable(self, enable):
        enable = enable and self.getParameter().getHintValue('showEditor', True)
        super(ColorParameterWidget, self)._setMasterWidgetEnable(enable)

    def _editWidgetValueChanged(self):
        super(ColorParameterWidget, self)._editWidgetValueChanged()
        color = self.getPyValue()
        self.colorLabel.setColor(color)


class Color3fWidget(ColorWidget):
    _valueSize = 3


class Color4fWidget(ColorWidget):
    _valueSize = 4


class Color3fParameterWidget(Color3fWidget, ColorParameterWidget):
    def __init__(self):
        super(Color3fParameterWidget, self).__init__()
        ParameterWidget.__init__(self)


class Color4fParameterWidget(Color4fWidget, ColorParameterWidget):
    def __init__(self):
        super(Color4fParameterWidget, self).__init__()
        ParameterWidget.__init__(self)

