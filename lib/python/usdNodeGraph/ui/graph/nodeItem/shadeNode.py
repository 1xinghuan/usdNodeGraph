# -*- coding: utf-8 -*-

from .nodeItem import NodeItem
from .usdNode import UsdNodeItem
from usdNodeGraph.ui.graph.other.port import ShaderInputPort, ShaderOutputPort
from usdNodeGraph.utils.log import get_logger


logger = get_logger('usdNodeGraph.shadeNode')


PORT_SPACING = 20


class _UsdShadeNodeItem(UsdNodeItem):
    reverse = False

    def __init__(self, *args, **kwargs):
        self.inputConnectionPorts = []
        self.outputConnectionPorts = []

        super(_UsdShadeNodeItem, self).__init__(*args, **kwargs)

    def _updateNameText(self):
        super(_UsdShadeNodeItem, self)._updateNameText()

        if self.nameItem is not None:
            self.nameItem.setY(10)

    def _updateLabelText(self):
        super(_UsdShadeNodeItem, self)._updateLabelText()

        if self.labelItem is not None:
            self.labelItem.setY(self.nameItem.pos().y() + self.nameItem.boundingRect().height())

    def addShaderPort(self, port):
        self.addPort(port)
        self.h += PORT_SPACING

        self.updatePortsPos()

    def removePort(self, port):
        if isinstance(port, ShaderInputPort):
            self.inputConnectionPorts.remove(port)
            self.h -= PORT_SPACING
        if isinstance(port, ShaderOutputPort):
            self.outputConnectionPorts.remove(port)
            self.h -= PORT_SPACING

        super(_UsdShadeNodeItem, self).removePort(port)

        self.updatePortsPos()

    def updatePortsPos(self):
        super(_UsdShadeNodeItem, self).updatePortsPos()

        bbox = self.boundingRect()

        for index, port in enumerate(self.inputConnectionPorts):
            port.setPos(
                bbox.left() - port.w / 2.0,
                30 + (index + 1) * PORT_SPACING
            )
        for index, port in enumerate(self.outputConnectionPorts):
            port.setPos(
                bbox.right() - port.w + port.w / 2.0,
                bbox.height() - (index + 1) * PORT_SPACING
            )

    def addShaderInputPort(self, portName, label=None, dataType=None):
        port = ShaderInputPort(name=portName, label=label, dataType=dataType)
        self.inputConnectionPorts.append(port)

        self.addShaderPort(port)

    def addShaderOutputPort(self, portName, label=None, dataType=None):
        port = ShaderOutputPort(name=portName, label=label, dataType=dataType)
        self.outputConnectionPorts.append(port)

        self.addShaderPort(port)

    def getShaderInputPort(self, name):
        for port in self.inputConnectionPorts:
            if port.name == name:
                return port

    def getShaderOutputPort(self, name):
        for port in self.outputConnectionPorts:
            if port.name == name:
                return port

    def _portConnectionChanged(self, port):
        super(_UsdShadeNodeItem, self)._portConnectionChanged(port)
        if isinstance(port, ShaderInputPort):
            parameter = self.parameter(port.name)
            if parameter is None:
                return
            connections = port.getConnections()
            if len(connections) == 0:
                parameter.breakConnect()
            elif len(connections) == 1:
                connectPort = connections[0]
                connectNode = connectPort.node()
                nodePrimPath = connectNode.getCurrentNodeItemPrimPath()
                connectPath = '{}.{}'.format(nodePrimPath, connectPort.name)
                parameter.setConnect(connectPath)
            else:
                logger.warning('Input Port {}.{} has more than one connection!'.format(self.name(), port.name))

    # def _addShaderPortFromParam(self, parameter, label):
    #     parameterName = parameter.name()
    #
    #     if parameterName.startswith(INPUT_ATTRIBUTE_PREFIX):
    #         self.addShaderInputPort(parameterName, label=label)
    #     if parameterName.startswith(OUTPUT_ATTRIBUTE_PREFIX):
    #         self.addShaderOutputPort(parameterName, label=label)

    def getCurrentNodeItemPrimPath(self, prim=None):
        if prim is None:
            upPrimPath = self._getUpPrimPath('')
            upPrimPath = upPrimPath.rstrip('/')
            primPath = upPrimPath
        else:
            primPath = prim.GetPath().pathString
        if primPath == '/':
            primPath = ''
        primName = self.parameter('primName').getValue()
        primPath = '{}/{}'.format(primPath, primName)
        return primPath


class MaterialNodeItem(_UsdShadeNodeItem):
    nodeItemType = 'MaterialNodeItem'

    # inputs: -> as OutputPort
    # outputs: -> as InputPort
    def addShaderInputPort(self, portName, label=None, dataType=None):
        port = ShaderOutputPort(name=portName, label=label, dataType=dataType)
        self.outputConnectionPorts.append(port)

        self.addShaderPort(port)

    def addShaderOutputPort(self, portName, label=None, dataType=None):
        port = ShaderInputPort(name=portName, label=label, dataType=dataType)
        self.inputConnectionPorts.append(port)

        self.addShaderPort(port)


class ShaderNodeItem(_UsdShadeNodeItem):
    nodeItemType = 'ShaderNodeItem'

    def afterAddToScene(self):
        self.nodeObject.resetParameters()


NodeItem.registerNodeItem(MaterialNodeItem)
NodeItem.registerNodeItem(ShaderNodeItem)

