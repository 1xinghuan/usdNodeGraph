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
from .nodeItem import NodeItem
import time
import re
import os
import logging


logger = logging.getLogger('usdNodeGraph.node')


class Node(QObject):
    parameterValueChanged = Signal(object, object)
    parameterAdded = Signal(object)
    parameterRemoved = Signal(object)

    _nodeTypes = {}
    nodeType = 'Node'
    nodeItem = NodeItem

    fillNormalColor = QColor(50, 60, 70)
    fillHighlightColor = QColor(230, 230, 100)
    borderNormalColor = QColor(50, 60, 70)
    borderHighlightColor = QColor(180, 180, 250)

    @classmethod
    def createItem(cls, nodeType, **kwargs):
        nodeClass = cls._nodeTypes.get(nodeType, Node)
        nodeItemClass = nodeClass.nodeItem
        item = nodeItemClass(nodeClass, **kwargs)
        return item

    @classmethod
    def getAllNodeClass(cls):
        return cls._nodeTypes.keys()

    @classmethod
    def setParameterDefault(cls, parameterName, value):
        cls.parameterDefaultDict.update({parameterName: value})

    def __init__(self, item=None):
        super(Node, self).__init__()

        self.item = item

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
            self.parameter(name).setValue(defaultValue, emitSignal=False)

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
        if name in ['x', 'y']:
            return True
        return False

    def getProperty(self, name):
        if name == 'x':
            return self.item.scenePos().x()
        if name == 'y':
            return self.item.scenePos().y()

    def _paramterValueChanged(self, parameter, value):
        self.parameterValueChanged.emit(parameter, value)
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
            # print('Parameter Exist! {}'.format(parameterName))
            return self.parameter(parameterName)

        parameterClass = ParameterRegister.getParameter(parameterType)
        if parameterClass is None:
            logger.warning('Un-Support Parameter Type in addParameter! {}: {}'.format(parameterName, parameterType))
            return

        parameter = parameterClass(
            parameterName,
            parent=self,
            value=defaultValue,
            **kwargs
        )
        self._parameters.update({parameterName: parameter})

        self.parameterAdded.emit(parameter)

        return parameter

    def removeParameter(self, parameterName):
        if parameterName in self._parameters:
            # parameter = self.parameter(parameterName)
            self._parameters.pop(parameterName)
            self.parameterRemoved.emit(parameterName)


def registerNode(nodeObjectClass):
    nodeType = nodeObjectClass.nodeType
    Node._nodeTypes[nodeType] = nodeObjectClass
    nodeObjectClass.parameterDefaultDict = {}


def setNodeDefault(nodeType, paramName, value):
    nodeClass = Node._nodeTypes.get(nodeType)
    if nodeClass is not None:
        nodeClass.setParameterDefault(paramName, value)


