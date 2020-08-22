# -*- coding: utf-8 -*-
# __author__ = 'XingHuan'
# 8/29/2018


from usdNodeGraph.module.sqt import *
from .port import InputPort, OutputPort, Port
from .tag import PixmapTag
from ..const import *
from usdNodeGraph.ui.parameter.parameter import (
    Parameter, TextParameter, FloatParameter, StringParameter, BoolParameter
)
from usdNodeGraph.utils.log import get_logger
from .nodeItem import NodeItem
from usdNodeGraph.ui.utils.log import LogWindow
import time
import re
import os


logger = get_logger('usdNodeGraph.node')


class Node(QtCore.QObject):
    parameterValueChanged = QtCore.Signal(object)
    parameterAdded = QtCore.Signal(object)
    parameterRemoved = QtCore.Signal(object)

    _nodeTypes = {}
    nodeType = 'Node'
    nodeItem = NodeItem

    fillNormalColor = QtGui.QColor(50, 60, 70)
    fillHighlightColor = QtGui.QColor(230, 230, 100)
    borderNormalColor = QtGui.QColor(50, 60, 70)
    borderHighlightColor = QtGui.QColor(180, 180, 250)

    @classmethod
    def createItem(cls, nodeType, **kwargs):
        nodeClass = cls._nodeTypes.get(nodeType, Node)
        nodeItemClass = nodeClass.nodeItem
        item = nodeItemClass(nodeClass, **kwargs)
        return item

    @classmethod
    def getAllNodeClassNames(cls):
        return cls._nodeTypes.keys()

    @classmethod
    def getAllNodeClass(cls):
        return cls._nodeTypes.values()

    @classmethod
    def setParameterDefault(cls, parameterName, value):
        cls.parameterDefaults.update({parameterName: value})

    @classmethod
    def addCallback(cls, callbackType, func):
        if callbackType not in cls.callbacks:
            cls.callbacks[callbackType] = []
        cls.callbacks[callbackType].append(func)

    def __init__(self, item=None):
        super(Node, self).__init__()

        self.item = item
        self._parameters = {}
        self._parametersName = []
        self._updateToDated = False

        self._initParameters()
        self._initDefaults()
        self._syncParameters()

    def _initParameters(self):
        self._parameters = {
            # 'id': StringParameter(name='id', defaultValue=str(hex(id(self))), parent=self, builtIn=True),
            'name': Parameter(name='name', defaultValue='', parent=self, builtIn=True),
            'label': TextParameter(name='label', defaultValue='', parent=self, builtIn=True),
            'x': FloatParameter(name='x', defaultValue=None, parent=self, builtIn=True, visible=False),
            'y': FloatParameter(name='y', defaultValue=None, parent=self, builtIn=True, visible=False),
            'disable': BoolParameter(name='disable', defaultValue=0, parent=self, builtIn=True),
        }
        self._parametersName = self._parameters.keys()
        self._parametersName.sort()

    def _initDefaults(self):
        for name in self.parameterDefaults.keys():
            defaultValue = self.parameterDefaults.get(name)
            self.parameter(name).setValueQuietly(defaultValue, override=False)
            self.parameter(name).setInheritValue(defaultValue)

    def _syncParameters(self):
        pass

    def parameter(self, parameterName):
        return self._parameters.get(parameterName)

    def hasParameter(self, name):
        return name in self._parameters

    def parameters(self):
        return [self._parameters.get(n) for n in self._parametersName]

    def Class(self):
        return self.nodeType

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

    def _executeCallbacks(self, callbackType, **kwargs):
        funcs = self.callbacks.get(callbackType, [])
        kwargs.update({'node': self, 'type': callbackType})
        for func in funcs:
            func(**kwargs)

    def _paramterValueChanged(self, parameter):
        logger.debug('{}, {}'.format(parameter.name(), parameter.getValue()))
        self.parameterValueChanged.emit(parameter)
        self._whenParamterValueChanged(parameter)
        self._executeCallbacks('parameterValueChanged', parameter=parameter)

    def _whenParamterValueChanged(self, parameter):
        if parameter.name() == 'name':
            self.item.scene()._afterNodeNameChanged(self.item)

    def addParameter(self, parameterName, parameterType, defaultValue=None, **kwargs):
        """
        :param parameterName:
        :param parameterType:
        :param defaultValue:
        :param custom:
        :return:
        """
        from usdNodeGraph.ui.parameter.register import ParameterRegister

        if self.hasParameter(parameterName):
            return self.parameter(parameterName)

        parameterClass = ParameterRegister.getParameter(parameterType)
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


def registerNode(nodeObjectClass):
    nodeType = nodeObjectClass.nodeType
    Node._nodeTypes[nodeType] = nodeObjectClass
    nodeObjectClass.parameterDefaults = {}
    nodeObjectClass.callbacks = {}


def setParamDefault(nodeType, paramName, value):
    nodeClass = Node._nodeTypes.get(nodeType)
    if nodeClass is not None:
        nodeClass.setParameterDefault(paramName, value)


def addNodeCallback(nodeType, callbackType, func):
    nodeClass = Node._nodeTypes.get(nodeType)
    if nodeClass is not None:
        nodeClass.addCallback(callbackType, func)


