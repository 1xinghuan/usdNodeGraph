from usdNodeGraph.module.sqt import *
from usdNodeGraph.state.core import GraphState


class LineEdit(QtWidgets.QLineEdit):
    def __init__(self, text=""):
        super(LineEdit, self).__init__()

        self.setFixedHeight(30)
        self.setText(text)
        self.setAlignment(QtCore.Qt.AlignHCenter)


class TimeSlider(QtWidgets.QSlider):
    def __init__(self):
        super(TimeSlider, self).__init__()

        self.setOrientation(QtCore.Qt.Horizontal)

        self._isHhover = False
        self._isMoving = False
        self.hoverValue = 1

        self.setMouseTracking(True)

        self.setMinimumHeight(50)

    def paintEvent(self, QPaintEvent):
        super(TimeSlider, self).paintEvent(QPaintEvent)

        painter = QtGui.QPainter(self)

        self._drawHover(painter)

    def _getPosition(self, percent):
        return percent * self.width() + 5 - 10 * percent

    def _getPercent(self, value):
        if self.maximum() > self.minimum():
            return float(value - self.minimum()) / (self.maximum() - self.minimum())
        else:
            return 1.0

    def _drawHover(self, painter):
        if self._isHhover:
            pen = QtGui.QPen(QtGui.QColor(220, 220, 220))
            pen.setWidth(2)
            painter.setPen(pen)
            length = 10
            percent = self._getPercent(self.hoverValue)
            positionX = self._getPosition(percent)
            y1 = (self.height() - length) / 2.0
            y2 = (self.height() - length) / 2.0 + length
            hoverline = QtCore.QLine(QtCore.QPoint(positionX, y1), QtCore.QPoint(positionX, y2))
            painter.drawLine(hoverline)
            text = str(self.hoverValue)
            font = QtGui.QFont("Arial", 10)
            fm = QtGui.QFontMetrics(font)
            textWidth = fm.boundingRect(text).width()
            painter.setFont(font)
            textX = positionX - textWidth / 2.0
            if textX + textWidth > self.width():
                textX = self.width() - textWidth
            if textX < 0:
                textX = 0
            painter.drawText(textX, y1 - 5, text)

    def enterEvent(self, *args, **kwargs):
        self._isHhover = True

    def leaveEvent(self, *args, **kwargs):
        self._isHhover = False

    def mousePressEvent(self, QMouseEvent):
        super(TimeSlider, self).mousePressEvent(QMouseEvent)
        pos = QMouseEvent.pos().x() / float(self.width())
        self.setValue(round(pos * (self.maximum() - self.minimum()) + self.minimum()))
        self._isMoving = True

    def mouseMoveEvent(self, QMouseEvent):
        super(TimeSlider, self).mouseMoveEvent(QMouseEvent)

        x = QMouseEvent.pos().x()
        precent = float(x) / self.width()
        self.hoverValue = int(round(self.minimum() + precent * (self.maximum() - self.minimum())))

        self.update()

        if self._isMoving:
            self.setValue(self.hoverValue)

    def mouseReleaseEvent(self, QMouseEvent):
        super(TimeSlider, self).mouseReleaseEvent(QMouseEvent)
        self._isMoving = False


class TimeSliderWidget(QtWidgets.QWidget):
    def __init__(self):
        super(TimeSliderWidget, self).__init__()

        self._stage = None

        self._initUI()

        self.frameInEdit.editingFinished.connect(self._frameInEditChanged)
        self.frameOutEdit.editingFinished.connect(self._frameOutEditChanged)
        self.timeSlider.valueChanged.connect(self._timeSliderValueChanged)

    def _initUI(self):
        self.masterLayout = QtWidgets.QHBoxLayout()
        self.masterLayout.setContentsMargins(10, 0, 10, 0)
        self.setLayout(self.masterLayout)

        self.frameInEdit = LineEdit()
        self.frameInEdit.setMaximumWidth(50)
        self.timeSlider = TimeSlider()
        self.frameOutEdit = LineEdit()
        self.frameOutEdit.setMaximumWidth(50)

        self.masterLayout.addWidget(self.frameInEdit)
        self.masterLayout.addWidget(self.timeSlider)
        self.masterLayout.addWidget(self.frameOutEdit)

        self.setMaximumHeight(70)

    def _frameInEditChanged(self):
        timeIn = float(self.frameInEdit.text())
        self.timeSlider.setMinimum(timeIn)
        GraphState.setTimeIn(timeIn, stage=self._stage)

    def _frameOutEditChanged(self):
        timeOut = float(self.frameOutEdit.text())
        self.timeSlider.setMaximum(timeOut)
        GraphState.setTimeOut(timeOut, stage=self._stage)

    def setStage(self, stage):
        self._stage = stage
        if stage is not None:
            self.setRange(GraphState.getTimeIn(stage), GraphState.getTimeOut(stage))
            self.setCurrentTime(GraphState.getCurrentTime(stage))

    def setRange(self, timeIn=0, timeOut=0):
        self.frameInEdit.setText(str(timeIn))
        self.frameOutEdit.setText(str(timeOut))
        self.timeSlider.setMinimum(timeIn)
        self.timeSlider.setMaximum(timeOut)

    def setCurrentTime(self, time):
        self.timeSlider.setValue(time)

    def _timeSliderValueChanged(self):
        GraphState.setCurrentTime(self.timeSlider.value(), stage=self._stage)

