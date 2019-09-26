# -*- coding: utf-8 -*-
# __author__ = 'XingHuan'


import copy
from usdNodeGraph.module.sqt import *


class Parameter(QObject):
    parameterTypeString = None
    valueTypeName = None
    parameterValueChanged = Signal(object, object)

    @classmethod
    def convertValueFromPy(cls, pyValue):
        return pyValue

    @classmethod
    def convertValueToPy(cls, usdValue):
        return usdValue

    @classmethod
    def convertTimeSamplesFromPy(cls, timeSamples):
        timeSamples = copy.deepcopy(timeSamples)
        for key, value in timeSamples.items():
            timeSamples[key] = cls.convertValueFromPy(value)
        return timeSamples

    @classmethod
    def convertTimeSamplesToPy(cls, timeSamples):
        pyTimeSamples = {}
        for key, value in timeSamples.items():
            pyTimeSamples[key] = cls.convertValueToPy(value)
        return timeSamples

    def __init__(
            self,
            name='',
            value=None,
            parent=None,
            timeSamples=None,
            builtIn=False,
            visible=True,
            label=None,
            order=None,
            custom=False,
            **kwargs
    ):
        super(Parameter, self).__init__()

        self._name = name
        self._label = name if label is None else label
        self._order = order
        self._node = parent
        self._value = value
        self._defaultValue = value
        self._timeSamples = timeSamples
        self._builtIn = builtIn
        self._visible = visible
        self._connect = None
        self._isCustom = custom

        self.parameterValueChanged.connect(self._node._paramterValueChanged)

    def hasKey(self):
        return self._timeSamples is not None

    def hasConnect(self):
        return self._connect is not None

    def getDefaultValue(self):
        return self._defaultValue

    def name(self):
        return self._name

    def node(self):
        return self._node

    def isBuiltIn(self):
        return self._builtIn

    def isVisible(self):
        return self._visible

    def getValue(self, time=None):
        if self._node.hasProperty(self._name):
            return self._node.getProperty(self._name)
        if not self.hasKey():
            return self._value
        else:
            if time is None:
                return self._timeSamples.values()[0]
            else:
                # todo: if time not in keys?
                return self._timeSamples.get(time)
    
    def getTimeSamples(self):
        return self._timeSamples

    def setTimeSamples(self, timeSamples, emitSignal=False):
        self._timeSamples = timeSamples
        if emitSignal:
            self.parameterValueChanged.emit(self, value)

    def setValue(self, value, emitSignal=True):
        self._value = value
        if emitSignal:
            self.parameterValueChanged.emit(self, value)
    
    def setValueAt(self, value, time=None):
        if self._timeSamples is None:
            self.setValue(value)
            return
        self._timeSamples.update({time: value})
        self.parameterValueChanged.emit(self, value)

    def setConnect(self, connect, emitSignal=True):
        self._connect = connect
        if emitSignal:
            self.parameterValueChanged.emit(self, None)

    def breakConnect(self):
        self._connect = None
        self.parameterValueChanged.emit(self, None)

    def isCustom(self):
        return self._isCustom

    def getConnect(self):
        return self._connect

    def setLabel(self, label):
        self._label = label

    def getLabel(self):
        return self._label

    def setOrder(self, order):
        self._order = order

    def getOrder(self):
        if self._order is not None:
            return self._order
        return self.getLabel()


