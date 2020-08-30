# -*- coding: utf-8 -*-
# __author__ = 'XingHuan'
# 8/29/2018

import traceback
from usdNodeGraph.module.sqt import *
from usdNodeGraph.ui.graph.other.port import InputPort, OutputPort
from usdNodeGraph.ui.graph.other.pipe import Pipe
from ..const import *
from usdNodeGraph.utils.log import get_logger
import re
from usdNodeGraph.core.node import Node

logger = get_logger('usdNodeGraph.nodeItem')


NAME_FONT = QtGui.QFont('Arial', 10, italic=True)
NAME_FONT.setBold(True)
LABEL_FONT = QtGui.QFont('Arial', 10)

EXPRESSION_VALUE_PATTERN = re.compile(r'\[value [^\[\]]+\]')
EXPRESSION_PYTHON_PATTERN = re.compile(r'\[python [^\[\]]+\]')


class _BaseNodeItem(QtWidgets.QGraphicsItem):
    x = 0
    y = 0
    w = 150
    h = 50

    labelNormalColor = QtGui.QColor(200, 200, 200)
    labelHighlightColor = QtGui.QColor(40, 40, 40)

    disablePenColor = QtGui.QColor(150, 20, 20)

    def __init__(self, nodeObjectClass, **kwargs):
        super(_BaseNodeItem, self).__init__()

        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)

        self.pipes = []
        self.ports = []
        self.panel = None

        self.margin = 6
        self.roundness = 10

        self._initUI()

        self.nodeObject = nodeObjectClass(item=self, **kwargs)

        self.fillColor = QtGui.QColor(*self.nodeObject.fillNormalColor)
        self.borderColor = QtGui.QColor(*self.nodeObject.borderNormalColor)

        self.nodeObject.parameterValueChanged.connect(self._paramterValueChanged)

    def parameter(self, parameterName):
        return self.nodeObject.parameter(parameterName)

    def hasParameter(self, name):
        return self.nodeObject.hasParameter(name)

    def parameters(self):
        return self.nodeObject.parameters()

    def addParameter(self, *args, **kwargs):
        return self.nodeObject.addParameter(*args, **kwargs)

    def Class(self):
        return self.nodeObject.Class()

    def name(self):
        return self.nodeObject.name()

    def _getInputsDict(self):
        return {}

    def _getOutputsDict(self):
        return {}

    def toDict(self):
        nodeName = self.parameter('name').getValue()
        paramsDict = {}
        for paramName, param in self.nodeObject._parameters.items():
            if paramName != 'name':
                override = param.isOverride()
                custom = param.isCustom()

                if not (override or custom) and paramName not in ['x', 'y']:
                    continue

                builtIn = param.isBuiltIn()
                visible = param.isVisible()

                timeSamplesDict = None
                value = None
                connect = None

                if param.hasConnect():
                    connect = param.getConnect()
                if param.hasKey():
                    timeSamples = param.getTimeSamples()
                    timeSamplesDict = {}
                    for t, v in timeSamples.items():
                        timeSamplesDict.update({t: param.convertValueToPy(v)})
                else:
                    value = param.convertValueToPy(param.getValue())

                paramDict = {'parameterType': param.parameterTypeString}
                if builtIn:
                    paramDict.update({'builtIn': builtIn})
                if not visible:
                    paramDict.update({'visible': False})
                if connect is not None:
                    paramDict.update({'connect': connect})
                if timeSamplesDict is not None:
                    paramDict.update({'timeSamples': timeSamplesDict})
                paramDict.update({'value': value})
                paramsDict.update({paramName: paramDict})

        inputsDict = self._getInputsDict()
        # outputsDict = self._getOutputsDict()

        data = {
            nodeName: {
                'parameters': paramsDict,
                'inputs': inputsDict,
                # 'outputs': outputsDict,
                'nodeClass': self.Class()
            }
        }

        return data

    @property
    def nodeType(self):
        return self.nodeObject.nodeType

    def _initUI(self):
        self.nameItem = None
        self.disableItem = None

    def _updateNameText(self):
        if self.nameItem is not None:
            name = self.parameter('name').getValue()
            self.nameItem.setText(name)

            rect = self.nameItem.boundingRect()
            self.nameItem.setX((self.w - rect.width()) / 2.0)
            self.nameItem.setY((self.h - rect.height()) / 2.0 - 10)

    def _updateDisableItem(self):
        disable = self.parameter('disable').getValue()
        if self.disableItem is None:
            self.disableItem = QtWidgets.QGraphicsLineItem(self)
            self.disablePen = QtGui.QPen(self.disablePenColor)
            self.disablePen.setWidth(5)
            self.disableItem.setPen(self.disablePen)
        self.disableItem.setLine(QtCore.QLineF(
            QtCore.QPointF(0, 0), QtCore.QPointF(self.w, self.h)
        ))
        self.disableItem.setVisible(disable)

    def _paramterValueChanged(self, parameter):
        if parameter.name() == 'x':
            self.setX(parameter.getValue())
        if parameter.name() == 'y':
            self.setY(parameter.getValue())
        if parameter.name() == 'disable':
            self._updateDisableItem()
        self._updateUI()

    def setLabelVisible(self, visible):
        if not visible and self.nameItem is None:
            return
        if visible and self.nameItem is None:
            self.nameItem = QtWidgets.QGraphicsSimpleTextItem(self)
            self.nameItem.setFont(NAME_FONT)
            self.nameItem.setBrush(DEFAULT_LABEL_COLOR)
        self.nameItem.setVisible(visible)
        if visible:
            self._updateNameText()

    def setPortsLabelVisible(self, visible):
        for port in self.ports:
            port.setLabelVisible(visible)

    def _updateUI(self):
        pass

    def forceUpdatePanelUI(self):
        if self.panel is not None:
            self.panel.updateUI()

    def _portConnectionChanged(self, port):
        pass

    def connectSource(self, node, inputName='input', outputName='output'):
        """
        input -> output
        :param node:
        :param inputName:
        :param outputName:
        :return:
        """
        inputPort = self.getInputPort(inputName)
        if inputPort is None:
            logger.warning('Input Port Not Exist! {}:{}'.format(node.name(), inputName))
            return

        outputPort = node.getOutputPort(outputName)
        if outputPort is None:
            logger.warning('Output Port Not Exist! {}{}'.format(node.name(), outputName))
            return

        inputPort.connectTo(outputPort)

    # def connectDestination(self, nodeItem, outputName='', inputName=''):
    #     pass

    def getInputPorts(self):
        return [port for port in self.ports if isinstance(port, InputPort)]

    def getOutputPorts(self):
        return [port for port in self.ports if isinstance(port, OutputPort)]

    def getInputPort(self, portName):
        for port in self.getInputPorts():
            if port.name == portName:
                return port

    def getOutputPort(self, portName):
        for port in self.getOutputPorts():
            if port.name == portName:
                return port

    def getPort(self, portName):
        for port in self.ports:
            if port.name == portName:
                return port

    def addPort(self, port):
        port.setParentItem(self)
        self.ports.append(port)
        port.portObj.connectChanged.connect(self._portConnectionChanged)

    def removePort(self, port):
        self.ports.remove(port)

    def addTag(self, tagItem, position=0.0):
        tagItem.setParentItem(self)
        margin_x = tagItem.w / 2.0 + TAG_MARGIN
        margin_y = tagItem.h / 2.0 + TAG_MARGIN
        if position <= 0.25:
            y = 0 - margin_y
            x = position * (self.w + margin_x * 2) / 0.25 - margin_x
        elif 0.25 < position <= 0.5:
            x = (self.w + margin_x * 2) - margin_x
            y = (position - 0.25) * (self.h + margin_y * 2.0) / 0.25 - margin_y
        elif 0.5 < position <= 0.75:
            x = (position - 0.5) * (-2.0 * margin_x - self.w) / 0.25 + (self.w + margin_x)
            y = self.h + margin_y
        elif 0.75 < position <= 1.0:
            x = 0 - margin_x
            y = (position - 0.75) * (-2.0 * margin_y - self.h) / 0.25 + (self.h + margin_y)
        tagItem.setPos(x - tagItem.w / 2.0, y - tagItem.h / 2.0)

    def setHighlight(self, value=True):
        self.fillColor = QtGui.QColor(*self.nodeObject.fillHighlightColor) if value else QtGui.QColor(*self.nodeObject.fillNormalColor)
        self.borderColor = QtGui.QColor(*self.nodeObject.borderHighlightColor) if value else QtGui.QColor(*self.nodeObject.borderNormalColor)
        if self.nameItem is not None:
            self.nameItem.setBrush(self.labelHighlightColor if value else self.labelNormalColor)

    def updatePipe(self):
        for port in self.ports:
            for pipe in port.pipes:
                pipe.updatePath()

    def setContextMenu(self):
        self._context_menus = []

    def _createContextMenu(self):
        self.setContextMenu()
        self.menu = QtWidgets.QMenu(self.scene().parent())
        for i in self._context_menus:
            action = QtWidgets.QAction(i[0], self.menu)
            action.triggered.connect(i[1])
            self.menu.addAction(action)

    def contextMenuEvent(self, event):
        super(_BaseNodeItem, self).contextMenuEvent(event)
        # self.menu.move(QCursor().pos())
        # self.menu.show()

    def boundingRect(self):
        rect = QtCore.QRectF(
            self.x,
            self.y,
            self.w,
            self.h)

        return rect

    def paint(self, painter, option, widget):
        if self.isSelected():
            penWidth = 2
        else:
            penWidth = 5
        self.setHighlight(self.isSelected())

        pen = QtGui.QPen(self.borderColor)
        pen.setWidth(penWidth)
        painter.setPen(pen)
        painter.setBrush(QtGui.QBrush(self.fillColor))

        painter.drawRoundedRect(self.x, self.y, self.w, self.h, self.roundness, self.roundness)

    def mouseMoveEvent(self, event):
        self.scene().updateSelectedNodesPipe()
        super(_BaseNodeItem, self).mouseMoveEvent(event)
        # slow
        # for n in self.scene().getSelectedNodes():
        #     n.parameter('x').setValue(n.scenePos().x())
        #     n.parameter('y').setValue(n.scenePos().y())

    def mouseDoubleClickEvent(self, event):
        super(_BaseNodeItem, self).mouseDoubleClickEvent(event)
        self.scene().parent().itemDoubleClicked.emit(self)

    def hoverEnterEvent(self, event):
        super(_BaseNodeItem, self).hoverEnterEvent(event)
        self.setToolTip(self.parameter('name').getValue())

    def _getInputsDict(self):
        inputs = {}
        for inputPort in self.getInputPorts():
            if len(inputPort.getConnections()) > 0:
                outputPort = inputPort.getConnections()[0]
                node = outputPort.node()
                inputs.update({
                    inputPort.name: [node.name(), outputPort.name]
                })
        return inputs


class NodeItem(_BaseNodeItem):
    _nodeItemsMap = {}
    nodeItemType = 'NodeItem'

    @classmethod
    def createItem(cls, nodeType, **kwargs):
        nodeClass = Node.getNodeClass(nodeType)
        nodeItemClass = cls._nodeItemsMap.get(nodeClass.nodeItemType)
        item = nodeItemClass(nodeClass, **kwargs)
        return item

    @classmethod
    def registerNodeItem(cls, itemClass):
        cls._nodeItemsMap.update(
            {itemClass.nodeItemType: itemClass}
        )

    def __init__(self, *args, **kwargs):
        self.inputPorts = []
        self.outputPorts = []

        self.findPipe = None
        self.findPos = None

        super(NodeItem, self).__init__(*args, **kwargs)

    def _initUI(self):
        super(NodeItem, self)._initUI()

        self.labelItem = None

        self.inputPort = InputPort(name='input')
        self.outputPort = OutputPort(name='output')
        self.inputPorts.append(self.inputPort)
        self.outputPorts.append(self.outputPort)
        self.addPort(self.inputPort)
        self.addPort(self.outputPort)

        self.updatePortsPos()

    def _updateLabelText(self):
        if self.labelItem is None:
            return

        label = self.parameter('label').getValue()

        expStrings = re.findall(EXPRESSION_VALUE_PATTERN, label)
        for expString in expStrings:
            paramName = ' '.join(expString.split(' ')[1:]).replace(']', '')
            param = self.parameter(paramName)
            if param is not None:
                paramValue = param.getValue()
                label = label.replace(expString, str(paramValue))

        expStrings = re.findall(EXPRESSION_PYTHON_PATTERN, label)
        for expString in expStrings:
            pyString = ' '.join(expString.split(' ')[1:]).replace(']', '')
            try:
                result = eval(pyString, globals(), Node._expressionMap)
            except Exception, e:
                result = e
            label = label.replace(expString, str(result))

        self.labelItem.setHtml(label)

        rect = self.labelItem.boundingRect()
        self.labelItem.setX((self.w - rect.width()) / 2.0)
        self.labelItem.setY(self.h / 2.0 + 0)

    def setLabelVisible(self, visible):
        super(NodeItem, self).setLabelVisible(visible)
        if not visible and self.labelItem is None:
            return
        if visible and self.labelItem is None:
            self.labelItem = QtWidgets.QGraphicsTextItem(self)
            self.labelItem.setFont(LABEL_FONT)
        self.labelItem.setVisible(visible)
        if visible:
            self._updateLabelText()

    def _updateUI(self):
        super(NodeItem, self)._updateUI()
        self._updateNameText()
        self._updateLabelText()

    def getSources(self):
        ports = []
        ports.extend(self.inputPort.getConnections())
        return [port.node() for port in ports]

    def getDestinations(self):
        ports = []
        ports.extend(self.outputPort.getConnections())
        return [port.node() for port in ports]

    def _setPortPos(self, port):
        bbox = self.boundingRect()
        if isinstance(port, InputPort):
            port.setPos((bbox.width() - port.w) / 2.0, bbox.top() - port.w / 2.0)
        elif isinstance(port, OutputPort):
            port.setPos((bbox.width() - port.w) / 2.0, bbox.bottom() - port.w / 2.0)

    def updatePortsPos(self):
        for port in self.inputPorts:
            self._setPortPos(port)
        for port in self.outputPorts:
            self._setPortPos(port)

    def connectToNode(self, node):
        self.inputPort.connectTo(node.outputPort)

    def _getUpPrimNode(self):
        sourceNodes = self.getSources()
        if len(sourceNodes) == 1:
            sourceNode = sourceNodes[0]
            if sourceNode.hasParameter('primName'):
                return sourceNode
            else:
                return sourceNode._getUpPrimNode()

    def _getUpPrimPath(self, path):
        upPrimNode = self._getUpPrimNode()
        if upPrimNode is None:
            return path
        upPrimPath = upPrimNode._getUpPrimPath(path)
        primName = upPrimNode.parameter('primName').getValue()
        return '{}/{}'.format(upPrimPath, primName)

    def afterAddToScene(self):
        pass

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.findingPipe = True
            self.startPos = self.mapToScene(self.boundingRect().center())

    def mouseMoveEvent(self, event):
        super(NodeItem, self).mouseMoveEvent(event)

        connectedPipes = []
        for port in self.ports:
            connectedPipes.extend(port.pipes)

        findPos = self.pos() + QtCore.QPointF(self.w / 2.0, -10)
        findItem = self.scene().itemAt(findPos, QtGui.QTransform())

        if isinstance(findItem, Pipe) and findItem not in connectedPipes:
            self.findPipe = findItem
            self.findPipe.setLineColor(highlight=True)
            self.findPipe.update()

            self.findPos = findPos
        else:
            if self.findPipe is not None:
                line = QtCore.QLineF(findPos, self.findPos)
                if line.length() > 10:
                    self.findPipe.setLineColor(highlight=False)
                    self.findPipe.update()
                    self.findingPipe = None

    def mouseReleaseEvent(self, event):
        super(NodeItem, self).mouseReleaseEvent(event)

        if self.findPipe is not None:
            source = self.findPipe.source
            target = self.findPipe.target

            self.findPipe.breakConnection()

            self.inputPort.connectTo(source)
            self.outputPort.connectTo(target)

            self.findPipe = None

