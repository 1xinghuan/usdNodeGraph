# -*- coding: utf-8 -*-
# __author__ = 'XingHuan'


import logging
from pxr import Usd, Sdf, Kind, UsdGeom
from usdNodeGraph.module.sqt import *
from .nodeItem import NodeItem
from .node import registerNode, setParamDefault
from usdNodeGraph.ui.parameter.parameter import Parameter, StringParameter
from .usdNode import UsdNode, UsdNodeItem
from .port import InputPort, OutputPort, ShaderInputPort, ShaderOutputPort
from usdNodeGraph.utils.const import INPUT_ATTRIBUTE_PREFIX, OUTPUT_ATTRIBUTE_PREFIX
from .sdr import SdrRegistry


logger = logging.getLogger('usdNodeGraph.shadeNode')


PORT_SPACING = 20


class _UsdShadeNodeItem(UsdNodeItem):
    fillNormalColor = QColor(50, 60, 80)
    borderNormalColor = QColor(200, 250, 200, 200)
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

    def _portConnectionChanged(self, port):
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
                nodePrimPath = connectNode.getCurrentPrimPath()
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


class _UsdShadeNode(UsdNode):
    nodeType = '_UsdShade'
    fillNormalColor = QColor(50, 60, 80)
    borderNormalColor = QColor(170, 250, 170, 200)
    reverse = False

    def __init__(self, prim=None, **kwargs):
        super(_UsdShadeNode, self).__init__(**kwargs)

        self.parameter('primName').setValue(self.name(), emitSignal=False)

        if prim is not None:
            attrKeys = prim.attributes.keys()
            attrKeys.sort()
            for index, name in enumerate(attrKeys):
                attribute = prim.attributes[name]
                self._addAttributeParameter(attribute)
            self.parameter('primName').setValue(prim.name, emitSignal=False)

    def _initParameters(self):
        super(_UsdShadeNode, self)._initParameters()
        param = self.addParameter('primName', 'string', defaultValue='')
        param.setOrder(-1)

    def _addAttributeParameter(self, attribute):
        attributeName = attribute.name
        attributeType = str(attribute.typeName)
        # attributeType = attribute.valueType.pythonClass
        # print attributeName,
        # print attribute.valueType

        param = self.addParameter(attributeName, attributeType, custom=True, connectable=True)
        if param is not None:
            if attribute.HasInfo('connectionPaths'):
                connectionPathList = attribute.connectionPathList.GetAddedOrExplicitItems()
                connect = connectionPathList[0]
                param.setConnect(connect.pathString, emitSignal=False)
            if attribute.HasInfo('timeSamples'):
                param.setTimeSamples(attribute.GetInfo('timeSamples'))
            else:
                param.setValue(attribute.default, emitSignal=False)

    def addParameter(self, *args, **kwargs):
        parameterName = args[0]
        connectable = kwargs.get('connectable', True)

        label = parameterName
        order = None
        if parameterName.startswith(INPUT_ATTRIBUTE_PREFIX):
            label = parameterName.replace(INPUT_ATTRIBUTE_PREFIX, '')
            order = len(self.item.inputConnectionPorts) + 1

        if parameterName.startswith(OUTPUT_ATTRIBUTE_PREFIX):
            label = parameterName.replace(OUTPUT_ATTRIBUTE_PREFIX, '')
            order = len(self.item.outputConnectionPorts) + 1 + 1000

        parameter = super(_UsdShadeNode, self).addParameter(label=label, order=order, *args, **kwargs)

        if parameter is not None and connectable:
            if parameterName.startswith(INPUT_ATTRIBUTE_PREFIX):
                self.item.addShaderInputPort(parameterName, label=label)
            if parameterName.startswith(OUTPUT_ATTRIBUTE_PREFIX):
                self.item.addShaderOutputPort(parameterName, label=label)

        return parameter

    def _paramterValueChanged(self, parameter, value):
        super(_UsdShadeNode, self)._paramterValueChanged(parameter, value)

        self.connectShader(parameter)

    def connectShader(self, parameter, emitSignal=False):
        paramName = parameter.name()
        paramPrefix = INPUT_ATTRIBUTE_PREFIX if self.Class() == 'Shader' else OUTPUT_ATTRIBUTE_PREFIX
        if paramName.startswith(paramPrefix):
            if parameter.hasConnect():
                connectPath = parameter.getConnect()
                connectPrimPath = connectPath.split('.')[0]
                connectParamName = connectPath.split('.')[1]
                inputPort = self.item.getShaderInputPort(paramName)
                connectNode = self.item.scene().getPrimNode(connectPrimPath)
                if connectNode is None:
                    return
                outputPort = connectNode.getPort(connectParamName)
                if outputPort is not None:
                    inputPort.connectTo(outputPort, emitSignal=emitSignal)

    def _execute(self, stage, prim):
        primPath = self.item.getCurrentPrimPath(prim)

        prim = stage.OverridePrim(primPath)
        prim.SetSpecifier(Sdf.SpecifierDef)
        prim.SetTypeName(self.nodeType)

        params = [param for param in self._parameters.values() if (not param.isBuiltIn() and param.name() not in ['primName'])]
        for param in params:
            # print(param.name(), param.getValue(), param.hasKey())
            if not param.hasConnect() and not param.hasKey():
                if param.getValue() == param.getDefaultValue():
                    continue
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
    # inputs: -> as OutputPort
    # outputs: -> as InputPort
    def addShaderInputPort(self, portName, label=None):
        port = ShaderOutputPort(name=portName, label=label)
        self.outputConnectionPorts.append(port)

        self.addShaderPort(port)

    def addShaderOutputPort(self, portName, label=None):
        port = ShaderInputPort(name=portName, label=label)
        self.inputConnectionPorts.append(port)

        self.addShaderPort(port)


class ShaderNodeItem(_UsdShadeNodeItem):
    def afterAddToScene(self):
        self.nodeObject.resetParameters()


class MaterialNode(_UsdShadeNode):
    nodeType = 'Material'
    nodeItem = MaterialNodeItem


class ShaderNode(_UsdShadeNode):
    nodeType = 'Shader'
    nodeItem = ShaderNodeItem
    borderNormalColor = QColor(250, 250, 150, 200)

    def __init__(self, prim=None, **kwargs):
        super(ShaderNode, self).__init__(prim=prim, **kwargs)

        self._oldShaderParameters = {}

        if prim is not None:
            for name, attribute in prim.attributes.items():
                if name == 'info:id':
                    self.parameter('info:id').setValue(attribute.default)
            self.parameter('primName').setValue(prim.name, emitSignal=False)

            for name, param in self._parameters.items():
                if name.startswith(INPUT_ATTRIBUTE_PREFIX) or name.startswith(OUTPUT_ATTRIBUTE_PREFIX):
                    self._oldShaderParameters[name] = param

    def _initParameters(self):
        super(ShaderNode, self)._initParameters()
        param = self.addParameter('info:id', 'choose', defaultValue='')
        param.setOrder(0)
        param.addItems(SdrRegistry.getNodeNames())

    def _paramterValueChanged(self, parameter, value):
        super(ShaderNode, self)._paramterValueChanged(parameter, value)

        if parameter.name() == 'info:id':
            if self.item.scene() is not None:
                self.resetParameters()

    def _clearParameters(self):
        removeNames = [name for name in self._parameters.keys() if name.startswith(INPUT_ATTRIBUTE_PREFIX) or name.startswith(OUTPUT_ATTRIBUTE_PREFIX)]

        for name in removeNames:
            self.removeParameter(name)
            port = self.item.getPort(name)
            if port is not None:
                port.destroy()

    def _addParameterFromProperty(self, paramName, property):
        if property is None:  # default out output
            connectable = True
            paramType = 'string'
            defaultValue = None
        else:
            connectable = property.IsConnectable()
            paramType = str(property.GetTypeAsSdfType()[0])
            defaultValue = property.GetDefaultValue()

        param = self.addParameter(
            paramName, paramType,
            defaultValue=defaultValue,
            custom=True, connectable=connectable
        )

        if param is not None:
            oldParam = self._oldShaderParameters.get(paramName)
            if oldParam is not None:
                if oldParam.hasConnect():
                    param.setConnect(oldParam.getConnect())
                elif param.parameterTypeString == oldParam.parameterTypeString:
                    if oldParam.hasKey():
                        param.setTimeSamples(oldParam.getTimeSamples())
                    else:
                        param.setValue(oldParam.getValue())

            return param

    def _addParametersFromShaderNode(self, shaderNode):
        inputNames = shaderNode.GetInputNames()
        inputNames.sort()
        outputNames = shaderNode.GetOutputNames()
        outputNames.sort()
        if len(outputNames) == 0:
            outputNames.append('out')

        for inputName in inputNames:
            input = shaderNode.GetInput(inputName)
            paramName = '{}{}'.format(INPUT_ATTRIBUTE_PREFIX, inputName)
            self._addParameterFromProperty(paramName, input)
        for outputName in outputNames:
            output = shaderNode.GetOutput(outputName)
            paramName = '{}{}'.format(OUTPUT_ATTRIBUTE_PREFIX, outputName)
            self._addParameterFromProperty(paramName, output)

        self.item.setLabelVisible(True)
        self.item.setPortsLabelVisible(True)

    def resetParameters(self):
        shaderName = self.parameter('info:id').getValue()
        shaderNode = SdrRegistry.getShaderNodeByName(shaderName)
        if shaderNode is not None:
            self._clearParameters()
            self._addParametersFromShaderNode(shaderNode)
        else:
            logger.warning('Can\'t get shader node information of {}'.format(shaderName))


registerNode(MaterialNode)
registerNode(ShaderNode)


setParamDefault(MaterialNode.nodeType, 'label', '/[value primName]')
setParamDefault(ShaderNode.nodeType, 'label', '/[value primName]')

