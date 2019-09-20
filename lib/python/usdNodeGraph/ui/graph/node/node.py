# -*- coding: utf-8 -*-
# __author__ = 'XingHuan'
# 8/29/2018


from usdNodeGraph.module.sqt import *
from .port import InputPort, OutputPort, Port
from .tag import PixmapTag
from ..const import *
from usdNodeGraph.ui.parameter.parameter import (
    Parameter, TextParameter, FloatParameter, StringParameter, BoolParameter)
import time
import re
import os


class Node(object):
    nodeType = 'Node'

    @classmethod
    def setParameterDefault(cls, parameterName, value):
        cls.parameterDefaultDict.update({parameterName: value})

    def __init__(self):
        super(Node, self).__init__()

        self._initParameters()
        self._initDefaults()

    def _initParameters(self):
        self._parameters = {
            # 'id': StringParameter(name='id', value=str(hex(id(self))), parent=self, builtIn=True),
            'name': Parameter(name='name', value='', parent=self, builtIn=True),
            'label': TextParameter(name='label', value='', parent=self, builtIn=True),
            'x': FloatParameter(name='x', value=None, parent=self, builtIn=True, visible=False),
            'y': FloatParameter(name='y', value=None, parent=self, builtIn=True, visible=False),
            'disable': BoolParameter(name='disable', value=0, parent=self, builtIn=True),
        }

    def _initDefaults(self):
        for name in self.parameterDefaultDict.keys():
            defaultValue = self.parameterDefaultDict.get(name)
            self.parameter(name).setValue(defaultValue)

    def parameter(self, parameterName):
        return self._parameters.get(parameterName)

    def hasParameter(self, name):
        return name in self._parameters

    def parameters(self):
        return [v for v in self._parameters.values()]

    def Class(self):
        return self.nodeType

    def name(self):
        return self.parameter('name').getValue()

    def hasProperty(self, name):
        return False

    def getProperty(self, name):
        return

    def _paramterValueChanged(self, parameter, value):
        pass

    def addParameter(self, parameterName, parameterType, defaultValue=None):
        from usdNodeGraph.ui.parameter.register import ParameterRegister

        if self.hasParameter(parameterName):
            print('Parameter Exist! {}'.format(parameterName))
            return self.parameter(parameterName)

        parameterClass = ParameterRegister.getParameter(parameterType)
        if parameterClass is None:
            print('Un-Support Parameter Type in addParameter! {}: {}'.format(parameterName, parameterType))
            return

        parameter = parameterClass(
            parameterName,
            parent=self,
            value=defaultValue
        )
        self._parameters.update({parameterName: parameter})

        return parameter

    def _getInputsDict(self):
        return {}

    def _getOutputsDict(self):
        return {}

    def toDict(self):
        nodeName = self.parameter('name').getValue()
        paramsDict = {}
        for paramName, param in self._parameters.items():
            if paramName != 'name':
                builtIn = param.isBuiltIn()
                visible = param.isVisible()
                timeSamplesDict = None
                value = None

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
                if timeSamplesDict is not None:
                    paramDict.update({'timeSamples': timeSamplesDict})
                paramDict.update({'value': value})
                if timeSamplesDict is not None or value != param.getDefaultValue():
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


class _BaseNodeItem(QGraphicsItem, Node):
    _nodeItemTypes = {}
    x = 0
    y = 0
    w = 150
    h = 50

    fillNormalColor = QColor(50, 60, 70)
    fillHighlightColor = QColor(230, 230, 100)
    borderNormalColor = QColor(50, 60, 70)
    borderHighlightColor = QColor(180, 180, 250)

    @classmethod
    def createItem(cls, nodeType, *args, **kwargs):
        item_class = cls._nodeItemTypes.get(nodeType, _BaseNodeItem)
        item = item_class(*args, **kwargs)
        return item

    @classmethod
    def getAllNodeClass(cls):
        return cls._nodeItemTypes.keys()

    def __init__(self, *args, **kwargs):
        super(_BaseNodeItem, self).__init__(*args, **kwargs)

        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)

        self.pipes = []
        self.ports = []

        self.margin = 6
        self.roundness = 10

        self.fillColor = self.fillNormalColor
        self.borderColor = self.borderNormalColor

        self._initUI()

        Node.__init__(self)

    def _initUI(self):
        self.nameItem = QGraphicsSimpleTextItem(self)

        self.labelFont = QFont('Arial', 10, italic=True)
        self.labelFont.setBold(True)

        self.nameItem.setFont(self.labelFont)
        self.nameItem.setBrush(DEFAULT_LABEL_COLOR)

    def _updateNameText(self, text):
        self.nameItem.setText(text)

    def _setLabelColor(self, color):
        self.nameItem.setBrush(color)
        # self.labelItem.setBrush(color)

    def _updateUI(self):
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
            print('Input Port Not Exist! {}'.format(inputName))
            return

        outputPort = node.getOutputPort(outputName)
        if outputPort is None:
            print('Output Port Not Exist! {}'.format(outputName))
            return

        inputPort.connectTo(outputPort)

    # def connectDestination(self, node, outputName='', inputName=''):
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

    def getSources(self):
        ports = []
        for inputPort in self.getInputPorts():
            ports.extend(inputPort.getConnections())
        return [port.node() for port in ports]

    def getDestinations(self):
        ports = []
        for outputPort in self.getOutputPorts():
            ports.extend(outputPort.getConnections())
        return [port.node() for port in ports]

    def addPort(self, port):
        port.setParentItem(self)
        self.ports.append(port)

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
        if value:
            self.fillColor = self.fillHighlightColor
            self.borderColor = self.borderHighlightColor
            self._setLabelColor(QColor(40, 40, 40))
        else:
            self.fillColor = self.fillNormalColor
            self.borderColor = self.borderNormalColor
            self._setLabelColor(QColor(200, 200, 200))

    def updatePipe(self):
        for port in self.ports:
            for pipe in port.pipes:
                pipe.updatePath()

    def setContextMenu(self):
        self._context_menus = []

    def _createContextMenu(self):
        self.setContextMenu()
        self.menu = QMenu(self.scene().parent())
        for i in self._context_menus:
            action = QAction(i[0], self.menu)
            action.triggered.connect(i[1])
            self.menu.addAction(action)

    def contextMenuEvent(self, event):
        super(_BaseNodeItem, self).contextMenuEvent(event)
        self.menu.move(QCursor().pos())
        self.menu.show()

    def boundingRect(self):
        rect = QRectF(
            self.x,
            self.y,
            self.w,
            self.h)

        return rect

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedHasChanged:
            self.setHighlight(self.isSelected())
        return super(_BaseNodeItem, self).itemChange(change, value)

    def paint(self, painter, option, widget):
        bbox = self.boundingRect()
        if self.isSelected():
            penWidth = 2
        else:
            penWidth = 5
        pen = QPen(self.borderColor)
        pen.setWidth(penWidth)
        painter.setPen(pen)
        painter.setBrush(QBrush(self.fillColor))

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

    def _paramterValueChanged(self, parameter, value):
        if parameter.name() == 'x':
            self.setX(value)
        if parameter.name() == 'y':
            self.setY(value)
        self._updateUI()

    def hasProperty(self, name):
        if name in ['x', 'y']:
            return True

    def getProperty(self, name):
        if name == 'x':
            return self.scenePos().x()
        if name == 'y':
            return self.scenePos().y()

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
    def __init__(self, *args, **kwargs):
        self.inputPorts = []
        self.outputPorts = []

        super(NodeItem, self).__init__(*args, **kwargs)

    def _initUI(self):
        super(NodeItem, self)._initUI()

        self.labelItem = QGraphicsTextItem(self)
        self.labelItem.setFont(self.labelFont)
        # self.labelItem.setBrush(DEFAULT_LABEL_COLOR)

        self.inputPort = InputPort(name='input')
        self.outputPort = OutputPort(name='output')
        self.inputPorts.append(self.inputPort)
        self.outputPorts.append(self.outputPort)
        self.addPort(self.inputPort)
        self.addPort(self.outputPort)

        self.updatePortsPos()

        self.disableItem = QGraphicsLineItem(self)
        self.disablePen = QPen(QColor(20, 20, 20))
        self.disablePen.setWidth(5)
        self.disableItem.setPen(self.disablePen)
        self.disableItem.setLine(QLineF(
            QPointF(0, 0), QPointF(self.w, self.h)
        ))

    def _updateLabelText(self, text):
        self.labelItem.setHtml(text)
        rect = self.labelItem.boundingRect()
        self.labelItem.setX((self.w - rect.width()) / 2.0)
        self.labelItem.setY(self.h / 2.0 + 0)

    def _updateNameText(self, text):
        super(NodeItem, self)._updateNameText(text)
        rect = self.nameItem.boundingRect()
        self.nameItem.setX((self.w - rect.width()) / 2.0)
        self.nameItem.setY((self.h - rect.height()) / 2.0 - 10)

    def _updateUI(self):
        name = self.parameter('name').getValue()
        label = self.parameter('label').getValue()

        expStrings = re.findall(r'\[value [^\[\]]+\]', label)
        for expString in expStrings:
            paramName = ' '.join(expString.split(' ')[1:]).replace(']', '')
            param = self.parameter(paramName)
            if param is not None:
                paramValue = param.getValue()
                label = label.replace(expString, str(paramValue))

        expStrings = re.findall(r'\[python [^\[\]]+\]', label)
        for expString in expStrings:
            pyString = ' '.join(expString.split(' ')[1:]).replace(']', '')
            try:
                result = eval(pyString)
            except:
                continue
            label = label.replace(expString, str(result))

        self._updateNameText(name)
        self._updateLabelText(label)
        self._updateDisableItem()

    def _updateDisableItem(self):
        disable = self.parameter('disable').getValue()
        self.disableItem.setVisible(disable)

    def getInputPorts(self):
        return self.inputPorts

    def getOutputPorts(self):
        return self.outputPorts

    def addPort(self, port):
        super(NodeItem, self).addPort(port)
        # self.updatePortsPos()

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


def registerNode(nodeClass):
    nodeType = nodeClass.nodeType
    NodeItem._nodeItemTypes[nodeType] = nodeClass
    nodeClass.parameterDefaultDict = {}


def setNodeDefault(nodeType, paramName, value):
    nodeClass = NodeItem._nodeItemTypes.get(nodeType)
    if nodeClass is not None:
        nodeClass.setParameterDefault(paramName, value)


