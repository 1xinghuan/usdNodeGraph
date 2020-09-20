# -*- coding: utf-8 -*-
# __author__ = 'XingHuan'
# 8/29/2018


from usdNodeGraph.module.sqt import *
from usdNodeGraph.ui.graph.other.pipe import Pipe, ConnectionPipe
from usdNodeGraph.core.state import GraphState

PORT_SIZE = 10
PORT_LABEL_COLOR = QtGui.QColor(200, 200, 200)


class PortObject(QtCore.QObject):
    connectChanged = QtCore.Signal(object)

    def __init__(self, item=None, *args, **kwargs):
        super(PortObject, self).__init__(*args, **kwargs)

        self._item = item

    def _connectChanged(self):
        self.connectChanged.emit(self._item)


class Port(QtWidgets.QGraphicsEllipseItem):
    orientation = 0
    x = 0
    y = 0
    w = PORT_SIZE
    h = PORT_SIZE

    fillColor = QtGui.QColor(230, 230, 0)
    borderNormalColor = QtGui.QColor(200, 200, 250)
    borderHighlightColor = QtGui.QColor(255, 255, 0)

    maxConnections = None

    def __init__(self, name='input', label=None, **kwargs):
        super(Port, self).__init__(**kwargs)

        self.portObj = PortObject(self)
        self.name = name
        self.label = label if label is not None else name
        self.pipes = []

        self.findingPort = False
        self.foundPort = None

        self.borderNormalWidth = 1
        self.borderHighlightWidth = 3
        self.borderColor = self.borderNormalColor
        self.borderWidth = self.borderNormalWidth

        self.nameItem = None

        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setAcceptDrops(True)
        self.setZValue(10)

        self.setRect(self.boundingRect())
        self._updateUI()

    def _updateUI(self):
        pen = QtGui.QPen(self.borderColor)
        pen.setWidth(self.borderWidth)
        self.setPen(pen)
        self.setBrush(QtGui.QBrush(self.fillColor))

    def setLabelVisible(self, visible):
        if not visible and self.nameItem is None:
            return
        if visible and self.nameItem is None:
            self.nameItem = QtWidgets.QGraphicsSimpleTextItem(self)
            self.nameItem.setBrush(PORT_LABEL_COLOR)
            self.nameItem.setText(self.label)
            self.nameRect = self.nameItem.boundingRect()
            self.nameTransform = QtGui.QTransform()
            self._setNameTransform()
            self.nameItem.setTransform(self.nameTransform)
        self.nameItem.setVisible(visible)

    def _setNameTransform(self):
        pass

    def node(self):
        return self.parentItem()

    def connectTo(self, port, emitSignal=True, connection=False):
        """
        inputPort -> outputPort
        :param port:
        :return:
        """
        if port is self:
            return

        for pipe in self.pipes:
            if (pipe.source == self and pipe.target == port) or (pipe.source == port and pipe.target == self):
                pipe.updatePath()
                return

        self._checkConnectionNumber()
        port._checkConnectionNumber()

        pipe = self.createPipe()
        if isinstance(self, InputPort):
            pipe.source = port
            pipe.target = self
        else:
            pipe.source = self
            pipe.target = port

        self.addPipe(pipe, emitSignal=emitSignal)
        port.addPipe(pipe, emitSignal=emitSignal)

        self.scene().addItem(pipe)

        pipe.updatePath()

    def addPipe(self, pipe, emitSignal=True):
        self.pipes.append(pipe)
        if emitSignal:
            self.portObj._connectChanged()

    def removePipe(self, pipe):
        if pipe in self.pipes:
            self.pipes.remove(pipe)
            self.portObj._connectChanged()

    def _checkConnectionNumber(self):
        if self.maxConnections is None:
            return
        if len(self.pipes) == self.maxConnections:
            pipe = self.pipes[0]
            self.removePipe(pipe)
            pipe.breakConnection()

    def boundingRect(self):
        rect = QtCore.QRectF(
            self.x,
            self.y,
            self.w,
            self.h
        )
        return rect

    def setHighlight(self, toggle):
        if toggle:
            self.borderColor = self.borderHighlightColor
            self.borderWidth = self.borderHighlightWidth
        else:
            self.borderColor = self.borderNormalColor
            self.borderWidth = self.borderNormalWidth
        self._updateUI()

    def destroy(self):
        pipesToDelete = self.pipes[::]  # Avoid shrinking during deletion.
        for pipe in pipesToDelete:
            self.removePipe(pipe)
            self.scene().removeItem(pipe)
        node = self.node()
        if node:
            node.removePort(self)

        self.scene().removeItem(self)
        del self

    def createPipe(self):
        if isinstance(self, (ShaderInputPort, ShaderOutputPort)):
            pipe = ConnectionPipe(orientation=self.orientation)
        else:
            pipe = Pipe(orientation=self.orientation)
        return pipe

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.findingPort = True
            # self.startPos = self.scenePos()
            self.startPos = self.mapToScene(self.boundingRect().center())
            self.floatPipe = self.createPipe()
            self.scene().addItem(self.floatPipe)

    def mouseMoveEvent(self, event):
        if self.findingPort:
            pos = event.pos()
            pos = pos - QtCore.QPointF(self.w / 2.0, self.h / 2.0)
            scenePos = self.startPos + pos
            if isinstance(self, InputPort):
                self.floatPipe.updatePath(scenePos, self.startPos)
            elif isinstance(self, OutputPort):
                self.floatPipe.updatePath(self.startPos, scenePos)

            findPort = self.scene().itemAt(scenePos, QtGui.QTransform())
            if findPort is not None and isinstance(findPort, Port) and not isinstance(findPort, self.__class__):
                self.foundPort = findPort
                self.foundPort.setHighlight(True)
            else:
                if self.foundPort is not None:
                    self.foundPort.setHighlight(False)
                    self.foundPort = None

    def _connectToFoundPort(self, event):
        pos = event.pos()
        pos = pos - QtCore.QPointF(self.w / 2.0, self.h / 2.0)
        scenePos = self.startPos + pos
        findPort = self.scene().itemAt(scenePos, QtGui.QTransform())
        if findPort is not None and isinstance(findPort, Port) and not isinstance(findPort, self.__class__):
            if self.name != findPort.name:
                self.connectTo(findPort)
        self.scene().removeItem(self.floatPipe)

        self.findingPort = False
        if self.foundPort is not None:
            self.foundPort.setHighlight(False)
            self.foundPort = None

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self.findingPort:
            with GraphState.stopLiveUpdate():
                self._connectToFoundPort(event)
            self.scene().liveUpdateRequired()


class InputPort(Port):
    fillColor = QtGui.QColor(40, 60, 100)

    def __init__(self, *args, **kwargs):
        super(InputPort, self).__init__(*args, **kwargs)
        self.setToolTip(self.name)

    def _setNameTransform(self):
        self.nameTransform.translate(
            (PORT_SIZE / 2.0 - self.nameRect.width() / 2.0),
            -(self.nameRect.height() + PORT_SIZE / 2.0)
        )

    def getConnections(self):
        return [pipe.source for pipe in self.pipes if pipe.target == self and pipe.source is not None]


class OutputPort(Port):
    fillColor = QtGui.QColor(50, 100, 80)

    def __init__(self, *args, **kwargs):
        super(OutputPort, self).__init__(*args, **kwargs)
        self.setToolTip(self.name)

    def _setNameTransform(self):
        self.nameTransform.translate(
            (PORT_SIZE / 2.0 - self.nameRect.width() / 2.0),
            PORT_SIZE
        )

    def getConnections(self):
        return [pipe.target for pipe in self.pipes if pipe.source == self]


class ShaderInputPort(InputPort):
    orientation = 1
    maxConnections = 1

    def _setNameTransform(self):
        self.nameTransform.translate(15, -(self.nameRect.height() / 2.0 - PORT_SIZE / 2.0))


class ShaderOutputPort(OutputPort):
    orientation = 1

    def _setNameTransform(self):
        self.nameTransform.translate(-self.nameRect.width() - 5, -(self.nameRect.height() / 2.0 - PORT_SIZE / 2.0))


