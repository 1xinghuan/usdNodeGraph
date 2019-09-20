# -*- coding: utf-8 -*-
# __author__ = 'XingHuan'


from pxr import Usd, Sdf, Kind, UsdGeom
from usdNodeGraph.module.sqt import *
from .node import NodeItem, registerNode, setNodeDefault, _BaseNodeItem
from usdNodeGraph.ui.parameter.parameter import Parameter, StringParameter
from .usdNode import UsdNodeItem
from .port import InputPort, OutputPort, ShaderInputPort, ShaderOutputPort
from usdNodeGraph.utils.const import INPUT_ATTRIBUTE_PREFIX, OUTPUT_ATTRIBUTE_PREFIX


PORT_SPACING = 20


class _UsdShadeNodeItem(UsdNodeItem):
    nodeType = '_UsdShade'
    fillNormalColor = QColor(50, 60, 80)
    borderNormalColor = QColor(200, 250, 200, 200)

    def __init__(self, prim=None, *args, **kwargs):
        super(_UsdShadeNodeItem, self).__init__(*args, **kwargs)

        self.inputConnectionPorts = []
        self.outputConnectionPorts = []

        if prim is not None:
            attrKeys = prim.attributes.keys()
            attrKeys.sort()
            for index, name in enumerate(attrKeys):
                attribute = prim.attributes[name]
                self._addAttributeParameter(attribute, index=index)
            self.parameter('primName').setValue(prim.name)

    def _initParameters(self):
        super(_UsdShadeNodeItem, self)._initParameters()
        param = self.addParameter('primName', 'string', defaultValue='')
        param.setOrder(-1)

    def _initUI(self):
        super(_UsdShadeNodeItem, self)._initUI()

    def _updateNameText(self, text):
        super(_UsdShadeNodeItem, self)._updateNameText(text)
        rect = self.nameItem.boundingRect()
        self.nameItem.setX((self.w - rect.width()) / 2.0)
        self.nameItem.setY(10)

    def _updateUI(self):
        name = self.parameter('name').getValue()
        self._updateNameText(name)
        self._updateDisableItem()

    def addShaderPort(self, port):
        self.addPort(port)
        self.h += PORT_SPACING

        bbox = self.boundingRect()

        if isinstance(port, ShaderInputPort):
            index = self.inputConnectionPorts.index(port)
            port.setPos(
                bbox.left() - port.w / 2.0,
                40 + index * PORT_SPACING
            )
        else:
            index = self.outputConnectionPorts.index(port)
            port.setPos(
                bbox.right() - port.w + port.w / 2.0,
                bbox.height() - index * PORT_SPACING - 30
            )

        self.updatePortsPos()

    def addShaderInputPort(self, portName, label=None):
        port = ShaderInputPort(name=portName, label=label)
        self.inputConnectionPorts.append(port)

        self.addShaderPort(port)

    def addShaderOutputPort(self, portName, label=None):
        port = ShaderOutputPort(name=portName, label=label)
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

    def _addAttributeParameter(self, attribute, index=-1):
        attributeName = attribute.name
        attributeType = str(attribute.typeName)
        # attributeType = attribute.valueType.pythonClass
        # print attributeName,
        # print attribute.valueType

        param = self.addParameter(attributeName, attributeType)
        if param is not None:
            if attribute.HasInfo('connectionPaths'):
                connectionPathList = attribute.connectionPathList.GetAddedOrExplicitItems()
                connect = connectionPathList[0]
                param.setConnect(connect.pathString)
            if attribute.HasInfo('timeSamples'):
                param.setTimeSamples(attribute.GetInfo('timeSamples'))
            else:
                param.setValue(attribute.default)

            if attributeName.startswith(INPUT_ATTRIBUTE_PREFIX):
                label = attributeName.replace(INPUT_ATTRIBUTE_PREFIX, '')
                param.setLabel(label)
                param.setOrder(index)

                self.addShaderInputPort(attributeName, label=label)
            if attributeName.startswith(OUTPUT_ATTRIBUTE_PREFIX):
                label = attributeName.replace(OUTPUT_ATTRIBUTE_PREFIX, '')
                param.setLabel(label)
                param.setOrder(index + 1000)

                self.addShaderOutputPort(attributeName, label=label)

            if attributeName == 'info:id':
                param.setOrder(0)

    def getCurrentPrimPath(self, prim=None):
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

    def _execute(self, stage, prim):
        primPath = self.getCurrentPrimPath(prim)

        prim = stage.OverridePrim(primPath)
        prim.SetSpecifier(Sdf.SpecifierDef)

        params = [param for param in self._parameters.values() if (not param.isBuiltIn() and param.name() not in ['primName'])]
        for param in params:
            # print(param.name(), param.getValue(), param.hasKey())
            attrName = param.name()
            if not prim.HasAttribute(attrName):
                attribute = prim.CreateAttribute(attrName, param.valueTypeName)
                attribute.SetCustom(False)
            else:
                attribute = prim.GetAttribute(attrName)

            if param.hasConnect():
                attribute.SetConnections([param.getConnect()])
            elif param.hasKey():
                for time, value in param.getTimeSamples().items():
                    attribute.Set(value, time)
            else:
                if param.getValue() is not None:
                    attribute.Set(param.getValue())
        return stage, prim


class MaterialNodeItem(_UsdShadeNodeItem):
    nodeType = 'Material'


class ShaderNodeItem(_UsdShadeNodeItem):
    nodeType = 'Shader'
    borderNormalColor = QColor(200, 250, 250, 200)


registerNode(MaterialNodeItem)
registerNode(ShaderNodeItem)


