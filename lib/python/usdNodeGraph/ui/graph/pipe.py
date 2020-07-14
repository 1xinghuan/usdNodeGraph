# -*- coding: utf-8 -*-
# __author__ = 'XingHuan'
# 8/29/2018


from usdNodeGraph.module.sqt import *
import math


PIPE_NORMAL_COLOR = QColor(130, 130, 130)
PIPE_HIGHTLIGHT_COLOR = QColor(250, 250, 100)


class Pipe(QGraphicsPathItem):
    """A connection between two versions"""
    normalColor = PIPE_NORMAL_COLOR
    lineStyle = None

    def __init__(self, orientation=0, **kwargs):
        super(Pipe, self).__init__(**kwargs)

        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.setAcceptHoverEvents(True)

        self.lineColor = self.normalColor
        self.thickness = 1.5
        self.pointAtLength = 7
        self.orientation = orientation

        self.source = None
        self.target = None
        self.isFloat = False
        self.foundPort = None

        self.curv1 = 0.5
        self.curv3 = 0.5

        self.curv2 = 0.0
        self.curv4 = 1.0

    def setLineColor(self, highlight=False, color=None):
        if color is not None:
            self.lineColor = color
            return
        if highlight:
            self.lineColor = PIPE_HIGHTLIGHT_COLOR
        else:
            self.lineColor = self.normalColor

    def updatePath(self, sourcePos=None, targetPos=None):
        orientation = self.orientation

        if self.source:
            sourcePos = self.source.mapToScene(self.source.boundingRect().center())
        if self.target:
            targetPos = self.target.mapToScene(self.target.boundingRect().center())
        if sourcePos is None or targetPos is None:
            return

        path = QPainterPath()
        path.moveTo(sourcePos)

        dx = targetPos.x() - sourcePos.x()
        dy = targetPos.y() - sourcePos.y()

        if orientation in [1, 3]:
            if (dx < 0 and orientation == 1) or (dx >= 0 and orientation == 3):
                self.curv1 = -0.5
                self.curv3 = 1.5
                self.curv2 = 0.2
                self.curv4 = 0.8
            else:
                self.curv1 = 0.5
                self.curv3 = 0.5
                self.curv2 = 0.0
                self.curv4 = 1.0
        elif orientation in [0, 2]:
            if (dy < 0 and orientation == 0) or (dy >= 0 and orientation == 2):
                self.curv1 = 0.2
                self.curv3 = 0.8
                self.curv2 = -0.5
                self.curv4 = 1.5
            else:
                self.curv1 = 0.0
                self.curv3 = 1.0
                self.curv2 = 0.5
                self.curv4 = 0.5

        ctrl1 = QPointF(
            sourcePos.x() + dx * self.curv1,
            sourcePos.y() + dy * self.curv2)
        ctrl2 = QPointF(
            sourcePos.x() + dx * self.curv3,
            sourcePos.y() + dy * self.curv4)

        path.cubicTo(ctrl1, ctrl2, targetPos)
        self.setPath(path)

    def breakConnection(self):
        if self.source is not None:
            self.source.removePipe(self)
            self.source = None
        if self.target is not None:
            self.target.removePipe(self)
            self.target = None

        if self.scene() is not None:
            self.scene().removeItem(self)

        del self

    def paint(self, painter, option, widget):
        zoom = self.scene().views()[0].currentZoom
        thickness = self.thickness / math.sqrt(zoom)
        pointAtLength = self.pointAtLength / math.sqrt(zoom)

        if self.isSelected():
            pen = QPen(PIPE_HIGHTLIGHT_COLOR, thickness)
        else:
            pen = QPen(self.lineColor, thickness)
        if self.lineStyle is not None:
            pen.setStyle(self.lineStyle)
        self.setPen(pen)
        self.setZValue(-1)
        super(Pipe, self).paint(painter, option, widget)

        center_pos = self.path().pointAtPercent(0.5)
        center_angle = self.path().angleAtPercent(0.5)

        painter.setPen(pen)
        painter.translate(center_pos)
        painter.rotate(180 - (center_angle + 30))
        painter.drawLine(QPointF(0, 0), QPointF(pointAtLength, 0))
        painter.rotate(60)
        painter.drawLine(QPointF(0, 0), QPointF(pointAtLength, 0))

    def _getDistance(self, currentPos):
        sourcePos = self.path().pointAtPercent(0)
        targetPos = self.path().pointAtPercent(1)
        dis1 = math.hypot(sourcePos.x() - currentPos.x(), sourcePos.y() - currentPos.y())
        dis2 = math.hypot(targetPos.x() - currentPos.x(), targetPos.y() - currentPos.y())
        minDis = 30
        if dis1 < minDis:
            return True, self.source
        if dis2 < minDis:
            return True, self.target
        return False, None

    def hoverEnterEvent(self, event):
        currentPos = event.pos()
        aroundPort, port = self._getDistance(currentPos)
        if aroundPort:
            self.setLineColor(True)
            self.update()

    def hoverLeaveEvent(self, event):
        self.setLineColor(False)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            currentPos = event.pos()
            self.startPos = currentPos
            aroundPort, port = self._getDistance(currentPos)
            if aroundPort:
                port.removePipe(self)
                if port == self.source:
                    self.source = None
                if port == self.target:
                    self.target = None
                self.isFloat = True
        else:
            super(Pipe, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        super(Pipe, self).mouseMoveEvent(event)

        from usdNodeGraph.ui.graph.node.port import Port
        currentPos = event.pos()
        if self.isFloat:
            if self.source is not None:
                self.updatePath(targetPos=currentPos)
            elif self.target is not None:
                self.updatePath(sourcePos=currentPos)

            findPort = self.scene().itemAt(currentPos, QTransform())
            if findPort is not None and isinstance(findPort, Port):
                self.foundPort = findPort
                self.foundPort.setHighlight(True)
            else:
                if self.foundPort is not None:
                    self.foundPort.setHighlight(False)
                    self.foundPort = None

    def mouseReleaseEvent(self, event):
        super(Pipe, self).mouseReleaseEvent(event)
        if self.isFloat:
            from .node.port import Port, InputPort, OutputPort

            scenePos = event.pos()
            findPort = self.scene().itemAt(scenePos, QTransform())

            self.breakConnection()

            if findPort is not None and isinstance(findPort, Port):
                if (isinstance(findPort, InputPort) and self.source is not None):
                    self.source.connectTo(findPort)
                elif (isinstance(findPort, OutputPort) and self.target is not None):
                    self.target.connectTo(findPort)

            self.isFloat = False
            if self.foundPort is not None:
                self.foundPort.setHighlight(False)
                self.foundPort = None


class ConnectionPipe(Pipe):
    lineStyle = Qt.DashLine
    normalColor = QColor(100, 130, 100)


