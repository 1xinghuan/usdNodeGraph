# -*- coding: utf-8 -*-
# __author__ = 'XingHuan'
# 8/29/2018


from usdNodeGraph.module.sqt import *
from ..pipe import Pipe
from ..const import Const

PORT_SIZE = 10


class Port(QGraphicsItem):
    orientation = 0
    x = 0
    y = 0
    w = PORT_SIZE
    h = PORT_SIZE

    def __init__(self, name='input', label=None, **kwargs):
        super(Port, self).__init__(**kwargs)

        self.name = name
        self.label = label if label is not None else name

        self.findingPort = False
        self.foundPort = None

        self.labelColor = QColor(10, 10, 10)

        self.fillColor = QColor(230, 230, 0)
        self.borderNormalColor = QColor(200, 200, 250)
        self.borderHighlightColor = QColor(255, 255, 0)
        self.borderNormalWidth = 1
        self.borderHighlightWidth = 3
        self.borderColor = self.borderNormalColor
        self.borderWidth = self.borderNormalWidth

        self.nameLabel = QGraphicsSimpleTextItem(self)
        self.nameLabel.setBrush(QColor(220, 220, 220))
        self.nameLabel.setText(self.label)
        self.nameRect = self.nameLabel.boundingRect()
        self.nameTransform = QTransform()
        self._setNameTransform()
        self.nameLabel.setTransform(self.nameTransform)

        self.pipes = []

        self.setCursor(Qt.PointingHandCursor)
        self.setAcceptDrops(True)

    def setLabelVisible(self, visible):
        self.nameLabel.setVisible(visible)

    def _setNameTransform(self):
        pass

    def node(self):
        return self.parentItem()

    def connectTo(self, port):
        """
        inputPort -> outputPort
        :param port:
        :return:
        """
        if port is self:
            return

        pipe = Pipe(orientation=self.orientation)
        if isinstance(self, InputPort):
            pipe.source = port
            pipe.target = self
        else:
            pipe.source = self
            pipe.target = port

        self.addPipe(pipe)
        port.addPipe(pipe)

        pipe.updatePath()

    def addPipe(self, pipe):
        self.pipes.append(pipe)
        scene = self.scene()
        if pipe not in scene.items():
            scene.addItem(pipe)

    def removePipe(self, pipe):
        if pipe in self.pipes:
            self.pipes.remove(pipe)

    def boundingRect(self):
        rect = QRectF(
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
        # self.setLabelVisible(toggle)
        self.update()

    def paint(self, painter, option, widget):
        bbox = self.boundingRect()
        pen = QPen(self.borderColor)
        pen.setWidth(self.borderWidth)
        painter.setPen(pen)
        painter.setBrush(QBrush(self.fillColor))
        painter.drawEllipse(bbox)

    def destroy(self):
        pipes_to_delete = self.pipes[::]  # Avoid shrinking during deletion.
        for pipe in pipes_to_delete:
            pipe.destroy()
        node = self.parentItem()
        if node:
            node.removePort(self)

        self.scene().removeItem(self)
        del self

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.findingPort = True
            # self.startPos = self.scenePos()
            self.startPos = self.mapToScene(self.boundingRect().center())
            self.floatPipe = Pipe(orientation=self.orientation)
            self.scene().addItem(self.floatPipe)

    def mouseMoveEvent(self, event):
        if self.findingPort:
            pos = event.pos()
            pos = pos - QPointF(self.w / 2.0, self.h / 2.0)
            scenePos = self.startPos + pos
            if isinstance(self, InputPort):
                self.floatPipe.updatePath(scenePos, self.startPos)
            elif isinstance(self, OutputPort):
                self.floatPipe.updatePath(self.startPos, scenePos)

            findPort = self.scene().itemAt(scenePos, QTransform())
            if findPort is not None and isinstance(findPort, Port) and not isinstance(findPort, self.__class__):
                self.foundPort = findPort
                self.foundPort.setHighlight(True)
            else:
                if self.foundPort is not None:
                    self.foundPort.setHighlight(False)
                    self.foundPort = None

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.findingPort:
            pos = event.pos()
            pos = pos - QPointF(self.w / 2.0, self.h / 2.0)
            scenePos = self.startPos + pos
            findPort = self.scene().itemAt(scenePos, QTransform())
            if findPort is not None and isinstance(findPort, Port) and not isinstance(findPort, self.__class__):
                if self.name != findPort.name:
                    self.connectTo(findPort)
            self.scene().removeItem(self.floatPipe)

            self.findingPort = False
            if self.foundPort is not None:
                self.foundPort.setHighlight(False)
                self.foundPort = None


class InputPort(Port):
    def __init__(self, *args, **kwargs):
        super(InputPort, self).__init__(*args, **kwargs)
        self.fillColor = kwargs.get("fillColor", QColor(40, 60, 100))
        self.setToolTip(self.name)

    def _setNameTransform(self):
        self.nameTransform.translate(
            (PORT_SIZE / 2.0 - self.nameRect.width() / 2.0),
            -(self.nameRect.height() + PORT_SIZE / 2.0)
        )

    def getConnections(self):
        return [pipe.source for pipe in self.pipes if pipe.target == self]


class OutputPort(Port):
    def __init__(self, *args, **kwargs):
        super(OutputPort, self).__init__(*args, **kwargs)
        self.fillColor = kwargs.get("fillColor", QColor(50, 100, 80))
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

    def _setNameTransform(self):
        self.nameTransform.translate(15, -(self.nameRect.height() / 2.0 - PORT_SIZE / 2.0))


class ShaderOutputPort(OutputPort):
    orientation = 1

    def _setNameTransform(self):
        self.nameTransform.translate(-self.nameRect.width() - 5, -(self.nameRect.height() / 2.0 - PORT_SIZE / 2.0))


