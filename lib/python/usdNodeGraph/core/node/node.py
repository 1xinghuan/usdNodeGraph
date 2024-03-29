# -*- coding: utf-8 -*-

from usdNodeGraph.module.sqt import *
from usdNodeGraph.ui.graph.const import *
from usdNodeGraph.core.parameter import (
    Parameter, StringParameter, TextParameter, FloatParameter, BoolParameter, Color4fParameter
)
from usdNodeGraph.utils.log import get_logger
from usdNodeGraph.ui.utils.log import LogWindow
from usdNodeGraph.core.state.core import GraphState

logger = get_logger('usdNodeGraph.node')


class NodeTypes(object):
    def __init__(self, nodeClass):
        self.nodeClass = nodeClass
        self.parentNodeClass = [n for n in nodeClass.__mro__ if hasattr(n, 'nodeType')]
        self.parentNodeTypes = [n.nodeType for n in self.parentNodeClass]

    def isSubType(self, nodeType):
        return nodeType in self.parentNodeTypes


class Node(QtCore.QObject):
    parameterValueChanged = QtCore.Signal(object)
    parameterAdded = QtCore.Signal(object)
    parameterRemoved = QtCore.Signal(object)
    parameterPagesCleared = QtCore.Signal()

    _nodeTypes = {}

    nodeType = 'Node'
    nodeItemType = 'NodeItem'
    nodeGroup = 'Other'

    fillNormalColor = (50, 60, 70)
    fillHighlightColor = (230, 230, 100)
    borderNormalColor = (50, 60, 70)
    borderHighlightColor = (180, 180, 250)

    _expressionMap = {}

    liveUpdateParameterNames = []

    @classmethod
    def convertColorToFloat(cls, color):
        return [i / 255.0 for i in color]

    @classmethod
    def convertColorTo255(cls, color):
        return [max(min(i * 255.0, 255.0), 0) for i in color]

    @classmethod
    def getLiveUpdateParameterNames(cls):
        return cls.liveUpdateParameterNames

    @classmethod
    def registerExpressionString(cls, string, object):
        cls._expressionMap[string] = object

    @classmethod
    def registerNode(cls, nodeObjectClass):
        nodeType = nodeObjectClass.nodeType
        cls._nodeTypes[nodeType] = nodeObjectClass
        nodeObjectClass.parameterDefaults = {}

    @classmethod
    def setParamDefault(cls, nodeType, paramName, value):
        nodeClass = cls._nodeTypes.get(nodeType)
        if nodeClass is not None:
            nodeClass.setParameterDefault(paramName, value)

    @classmethod
    def getAllNodeClassNames(cls):
        return list(cls._nodeTypes.keys())

    @classmethod
    def getAllNodeClass(cls):
        return list(cls._nodeTypes.values())

    @classmethod
    def setParameterDefault(cls, parameterName, value):
        cls.parameterDefaults.update({parameterName: value})

    @classmethod
    def getNodeClass(cls, nodeType):
        return cls._nodeTypes.get(nodeType, cls)

    @classmethod
    def getNodesByGroup(cls):
        result = {}
        for k, v in cls._nodeTypes.items():
            if v.nodeGroup not in result:
                result[v.nodeGroup] = []
            result[v.nodeGroup].append(v)
        return result

    @classmethod
    def Class(cls):
        return cls.nodeType

    @classmethod
    def NodeTypes(cls):
        return NodeTypes(cls)

    def __init__(self, item=None):
        super(Node, self).__init__()

        self.item = item
        self._parameters = {}
        self._parametersName = []
        self._updateToDated = False

        self._initParameters()
        self._initDefaults()
        self._syncParameters()
        self._setTags()

    def _initParameters(self):
        self._parameters = {
            # 'id': StringParameter(name='id', defaultValue=str(hex(id(self))), parent=self, builtIn=True),
            'name': StringParameter(name='name', defaultValue='', parent=self, builtIn=True, hints={'tab': 'None'}),
            'label': TextParameter(name='label', defaultValue='', parent=self, builtIn=True, hints={'tab': 'Node'}),
            'x': FloatParameter(name='x', defaultValue=None, parent=self, builtIn=True, visible=False, hints={'tab': 'Node'}),
            'y': FloatParameter(name='y', defaultValue=None, parent=self, builtIn=True, visible=False, hints={'tab': 'Node'}),
            'locked': BoolParameter(name='locked', defaultValue=False, parent=self, builtIn=True, visible=False, hints={'tab': 'Node'}),
            'disable': BoolParameter(name='disable', defaultValue=0, parent=self, builtIn=True, hints={'tab': 'Node'}),
            'fillColor': Color4fParameter(name='fillColor', parent=self, builtIn=True, hints={'showEditor': 'False', 'tab': 'None'}, defaultValue=self.convertColorToFloat(self.fillNormalColor)),
            'borderColor': Color4fParameter(name='borderColor', parent=self, builtIn=True, hints={'showEditor': 'False', 'tab': 'None'}, defaultValue=self.convertColorToFloat(self.borderNormalColor)),
        }
        self._parametersName = list(self._parameters.keys())
        self._parametersName.sort()

    def _initDefaults(self):
        for name in self.parameterDefaults.keys():
            defaultValue = self.parameterDefaults.get(name)
            self.parameter(name).setValueQuietly(defaultValue, override=False)
            self.parameter(name).setInheritValue(defaultValue)

    def _syncParameters(self):
        pass

    def _setTags(self):
        pass

    def parameter(self, parameterName):
        return self._parameters.get(parameterName)

    def hasParameter(self, name):
        return name in self._parameters

    def parameters(self):
        return [self._parameters.get(n) for n in self._parametersName]

    def name(self):
        return self.parameter('name').getValue()

    def hasProperty(self, name):
        if name in ['x', 'y']:
            return True
        return False

    def getProperty(self, name):
        if name == 'x':
            return self.item.scenePos().x()
        if name == 'y':
            return self.item.scenePos().y()

    def _paramterValueChanged(self, parameter):
        logger.debug('{}, {}'.format(parameter.name(), parameter.getValue()))
        self.parameterValueChanged.emit(parameter)
        self._whenParamterValueChanged(parameter)
        GraphState.executeCallbacks(
            'parameterValueChanged',
            node=self, parameter=parameter
        )

    def _whenParamterValueChanged(self, parameter):
        if parameter.name() == 'name':
            self.item.scene()._afterNodeNameChanged(self.item)
        if parameter.name() in self.getLiveUpdateParameterNames():
            self._liveUpdateRequired()

    def _liveUpdateRequired(self):
        self.item.scene().liveUpdateRequired()

    def addParameter(self, parameterName, parameterType, defaultValue=None, **kwargs):
        """
        :param parameterName:
        :param parameterType:
        :param defaultValue:
        :param custom:
        :return:
        """

        if self.hasParameter(parameterName):
            return self.parameter(parameterName)

        parameterClass = Parameter.getParameter(parameterType)
        if parameterClass is None:
            message = 'Un-Support Parameter Type in addParameter! {}: {}'.format(parameterName, parameterType)
            LogWindow.warning(message)
            logger.warning(message)
            return

        parameter = parameterClass(
            parameterName,
            parent=self,
            defaultValue=defaultValue,
            **kwargs
        )
        self._parameters.update({parameterName: parameter})
        self._parametersName.append(parameterName)

        self.parameterAdded.emit(parameter)

        return parameter

    def removeParameter(self, parameterName):
        if parameterName in self._parameters:
            # parameter = self.parameter(parameterName)
            self._parameters.pop(parameterName)
            self._parametersName.remove(parameterName)
            self.parameterRemoved.emit(parameterName)

    def clearPages(self):
        self.parameterPagesCleared.emit()

    def isNodeLocked(self):
        return self.parameter('locked').getValue()


import os

Node.registerExpressionString('os', os)

