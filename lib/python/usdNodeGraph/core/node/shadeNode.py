# -*- coding: utf-8 -*-
# __author__ = 'XingHuan'


from pxr import Sdf
from usdNodeGraph.module.sqt import *
from .node import Node
from .usdNode import UsdNode
from usdNodeGraph.utils.const import INPUT_ATTRIBUTE_PREFIX, OUTPUT_ATTRIBUTE_PREFIX
from usdNodeGraph.utils.log import get_logger
from usdNodeGraph.core.node.sdr import SdrRegistry


logger = get_logger('usdNodeGraph.shadeNode')


PORT_SPACING = 20


class _UsdShadeNode(UsdNode):
    nodeType = '_UsdShade'
    fillNormalColor = (30, 40, 70)
    borderNormalColor = (170, 250, 170, 200)
    reverse = False

    def __init__(self, primSpec=None, **kwargs):
        self._primSpec = primSpec
        super(_UsdShadeNode, self).__init__(**kwargs)

        self.parameter('primName').setValueQuietly(self.name())

        if self._primSpec is not None:
            attrKeys = self._primSpec.attributes.keys()
            attrKeys.sort()
            for index, name in enumerate(attrKeys):
                attribute = self._primSpec.attributes[name]
                self._addAttributeParameter(attribute)
            self.parameter('primName').setValueQuietly(self._primSpec.name)

    def _initParameters(self):
        super(_UsdShadeNode, self)._initParameters()
        param = self.addParameter('primName', 'string', defaultValue='')
        # param.setOrder(-1)

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
                param.setConnectQuietly(connect.pathString)
            if attribute.HasInfo('timeSamples'):
                param.setTimeSamples(attribute.GetInfo('timeSamples'))
            else:
                param.setValueQuietly(attribute.default)

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

    def _paramterValueChanged(self, parameter):
        super(_UsdShadeNode, self)._paramterValueChanged(parameter)

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
        primPath = self.item.getCurrentNodeItemPrimPath(prim)

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


class MaterialNode(_UsdShadeNode):
    nodeType = 'Material'
    nodeItemType = 'MaterialNodeItem'


class ShaderNode(_UsdShadeNode):
    nodeType = 'Shader'
    nodeItemType = 'ShaderNodeItem'
    borderNormalColor = (250, 250, 150, 200)

    def __init__(self, primSpec=None, **kwargs):
        super(ShaderNode, self).__init__(primSpec=primSpec, **kwargs)

        self._oldShaderParameters = {}

        if primSpec is not None:
            for name, attribute in primSpec.attributes.items():
                if name == 'info:id':
                    self.parameter('info:id').setValueQuietly(attribute.default)
            self.parameter('primName').setValueQuietly(primSpec.name)

            for name, param in self._parameters.items():
                if name.startswith(INPUT_ATTRIBUTE_PREFIX) or name.startswith(OUTPUT_ATTRIBUTE_PREFIX):
                    self._oldShaderParameters[name] = param

    def _initParameters(self):
        super(ShaderNode, self)._initParameters()
        param = self.addParameter('info:id', 'choose', defaultValue='')
        # param.setOrder(0)
        param.addItems(SdrRegistry.getNodeNames())

    def _paramterValueChanged(self, parameter):
        super(ShaderNode, self)._paramterValueChanged(parameter)

        if parameter.name() == 'info:id':
            if self.item.scene() is not None:
                self.resetParameters()
                self.item.forceUpdatePanelUI()

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
            # sometimes this return False but the attribute has connect so always return True here
            connectable = True
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
                    param.setConnectQuietly(oldParam.getConnect())
                elif param.parameterTypeString == oldParam.parameterTypeString:
                    if oldParam.hasKey():
                        param.setTimeSamples(oldParam.getTimeSamples())
                    else:
                        param.setValueQuietly(oldParam.getValue())

            return param

    def _addParametersFromShaderNode(self, shaderNode):
        inputNames = shaderNode.GetInputNames()
        outputNames = shaderNode.GetOutputNames()
        inputNames.sort()
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
            logger.warning('Can\'t get shader nodeItem information of {}'.format(shaderName))


Node.registerNode(MaterialNode)
Node.registerNode(ShaderNode)


Node.setParamDefault(MaterialNode.nodeType, 'label', '/[value primName]')
Node.setParamDefault(ShaderNode.nodeType, 'label', '/[value primName]')

