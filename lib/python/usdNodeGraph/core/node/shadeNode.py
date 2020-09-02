# -*- coding: utf-8 -*-
# __author__ = 'XingHuan'


from pxr import Sdf
from usdNodeGraph.module.sqt import *
from .node import Node
from .usdNode import UsdNode, _AttributeNode, _PrimAttributeNode
from ..parameter.params import TokenParameter
from usdNodeGraph.utils.const import INPUT_ATTRIBUTE_PREFIX, OUTPUT_ATTRIBUTE_PREFIX
from usdNodeGraph.utils.log import get_logger
from usdNodeGraph.core.node.sdr import SdrRegistry


logger = get_logger('usdNodeGraph.shadeNode')


PORT_SPACING = 20


class _UsdShadeNode(_PrimAttributeNode):
    nodeType = '_UsdShade'
    fillNormalColor = (30, 40, 70)
    borderNormalColor = (170, 250, 170, 200)
    reverse = False

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

        kwargs['label'] = label
        kwargs['order'] = order
        parameter = super(_UsdShadeNode, self).addParameter(*args, **kwargs)

        if parameter is not None and connectable:
            if parameterName.startswith(INPUT_ATTRIBUTE_PREFIX):
                self.item.addShaderInputPort(parameterName, label=label)
            if parameterName.startswith(OUTPUT_ATTRIBUTE_PREFIX):
                self.item.addShaderOutputPort(parameterName, label=label)

        return parameter

    def _whenParamterValueChanged(self, parameter):
        super(_UsdShadeNode, self)._whenParamterValueChanged(parameter)

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


class MaterialNode(_UsdShadeNode):
    nodeType = 'Material'
    nodeItemType = 'MaterialNodeItem'
    typeName = 'Material'


class ShaderNode(_UsdShadeNode):
    nodeType = 'Shader'
    nodeItemType = 'ShaderNodeItem'
    borderNormalColor = (250, 250, 150, 200)
    typeName = 'Shader'

    def __init__(self, *args, **kwargs):
        super(ShaderNode, self).__init__(*args, **kwargs)

    def _syncParameters(self):
        super(ShaderNode, self)._syncParameters()

        self._oldShaderParameters = {}

        if self._primSpec is not None:
            for name, param in self._parameters.items():
                if name.startswith(INPUT_ATTRIBUTE_PREFIX) or name.startswith(OUTPUT_ATTRIBUTE_PREFIX):
                    self._oldShaderParameters[name] = param

    def _initParameters(self):
        super(ShaderNode, self)._initParameters()
        param = self.addParameter('info:id', 'choose', defaultValue='')
        param.valueTypeName = TokenParameter.valueTypeName
        param.addItems(SdrRegistry.getNodeNames())

    def _whenParamterValueChanged(self, parameter):
        super(ShaderNode, self)._whenParamterValueChanged(parameter)

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
                param._metadata = oldParam._metadata
                if oldParam.hasConnect():
                    param.setConnectQuietly(oldParam.getConnect())
                elif (
                        (param.parameterTypeString == oldParam.parameterTypeString)
                        or (param.getValueDefault() == oldParam.getValueDefault())
                ):
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

