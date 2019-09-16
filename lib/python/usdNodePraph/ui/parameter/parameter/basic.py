# -*- coding: utf-8 -*-
# __author__ = 'XingHuan'


from usdNodePraph.module.sqt import *


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

    def __init__(
            self,
            name='',
            value=None,
            parent=None,
            timeSamples=None,
            builtIn=False
    ):
        super(Parameter, self).__init__()

        self._name = name
        self._node = parent
        self._value = value
        self._defaultValue = value
        self._timeSamples = timeSamples
        self._builtIn = builtIn

        self.parameterValueChanged.connect(self._node._paramterValueChanged)

    def hasKey(self):
        return self._timeSamples is not None

    def getDefaultValue(self):
        return self._defaultValue

    def name(self):
        return self._name

    def node(self):
        return self._node

    def isBuiltIn(self):
        return self._builtIn

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

    def setTimeSamples(self, timeSamples):
        self._timeSamples = timeSamples
        # self.parameterValueChanged.emit(self, value)

    def setValue(self, value):
        self._value = value
        self.parameterValueChanged.emit(self, value)
    
    def setValueAt(self, value, time=None):
        if self._timeSamples is None:
            self.setValue(value)
            return
        self._timeSamples.update({time, value})
        self.parameterValueChanged.emit(self, value)


