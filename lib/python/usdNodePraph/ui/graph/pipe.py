# -*- coding: utf-8 -*-
# __author__ = 'XingHuan'
# 8/29/2018


from usdNodePraph.module.sqt import *
import math


class Pipe(QGraphicsPathItem):
    """A connection between two versions"""

    def __init__(self, **kwargs):
        super(Pipe, self).__init__(**kwargs)

        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.setAcceptHoverEvents(True)

        self.normal_color = QColor(130, 130, 130)
        self.highlight_color = QColor(250, 250, 100)
        self.line_color = self.normal_color
        self.thickness = 1.5
        self.point_at_length = 7

        self.source = None
        self.target = None
        self.isFloat = False

        self.curv1 = 0.5
        self.curv3 = 0.5

        self.curv2 = 0.0
        self.curv4 = 1.0

    def set_line_color(self, highlight=False, color=None):
        if color is not None:
            self.line_color = color
            return
        if highlight:
            self.line_color = self.highlight_color
        else:
            self.line_color = self.normal_color

    def update_path(self, sourcePos=None, targetPos=None):
        if self.source:
            sourcePos = self.source.mapToScene(self.source.boundingRect().center())
        if self.target:
            targetPos = self.target.mapToScene(self.target.boundingRect().center())

        path = QPainterPath()
        path.moveTo(sourcePos)

        dx = targetPos.x() - sourcePos.x()
        dy = targetPos.y() - sourcePos.y()

        orientation = 0
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

    def break_connection(self):
        if self.source is not None:
            self.source.removePipe(self)
        if self.target is not None:
            self.target.removePipe(self)

    def paint(self, painter, option, widget):
        zoom = self.scene().views()[0].currentZoom
        thickness = self.thickness / math.sqrt(zoom)
        point_at_length = self.point_at_length / math.sqrt(zoom)

        if self.isSelected():
            pen = QPen(self.highlight_color, thickness)
        else:
            pen = QPen(self.line_color, thickness)
        self.setPen(pen)
        self.setZValue(-1)
        super(Pipe, self).paint(painter, option, widget)

        center_pos = self.path().pointAtPercent(0.5)
        center_angle = self.path().angleAtPercent(0.5)

        painter.setPen(pen)
        painter.translate(center_pos)
        painter.rotate(180 - (center_angle + 30))
        painter.drawLine(QPointF(0, 0), QPointF(point_at_length, 0))
        painter.rotate(60)
        painter.drawLine(QPointF(0, 0), QPointF(point_at_length, 0))

    def get_distance(self, currentPos):
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
        aroundPort, port = self.get_distance(currentPos)
        if aroundPort:
            self.set_line_color(True)
            self.update()

    def hoverLeaveEvent(self, event):
        self.set_line_color(False)
        self.update()

    def mousePressEvent(self, event):
        currentPos = event.pos()
        self.startPos = currentPos
        aroundPort, port = self.get_distance(currentPos)
        if aroundPort:
            port.removePipe(self)
            if port == self.source:
                self.source = None
            if port == self.target:
                self.target = None
            self.isFloat = True

    def mouseMoveEvent(self, event):
        currentPos = event.pos()
        if self.isFloat:
            if self.source is not None:
                self.update_path(targetPos=currentPos)
            elif self.target is not None:
                self.update_path(sourcePos=currentPos)

    def mouseReleaseEvent(self, event):
        if self.isFloat:
            from .node.port import Port, InputPort, OutputPort

            scenePos = event.pos()
            findPort = self.scene().itemAt(scenePos, QTransform())
            if findPort is not None and isinstance(findPort, Port):
                if (isinstance(findPort, InputPort) and self.source is not None):
                    self.source.connectTo(findPort)
                elif (isinstance(findPort, OutputPort) and self.target is not None):
                    self.target.connectTo(findPort)

            self.break_connection()
            self.scene().removeItem(self)

            self.isFloat = False


