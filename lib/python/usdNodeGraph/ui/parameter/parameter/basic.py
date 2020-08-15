# -*- coding: utf-8 -*-
# __author__ = 'XingHuan'


import copy
from pxr import Gf
from usdNodeGraph.module.sqt import *


class Parameter(QtCore.QObject):
    parameterTypeString = None
    valueTypeName = None
    valueChanged = QtCore.Signal(object)

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
        return pyTimeSamples

    @classmethod
    def getIntervalValue(cls, timeSamples, time):
        keys = timeSamples.keys()
        keys.sort()
        if time <= keys[0]:
            return timeSamples[keys[0]]
        elif time >= keys[-1]:
            return timeSamples[keys[-1]]
        else:
            beforeKey = None
            afterKey = None
            for k in keys:
                if k < time:
                    beforeKey = k
                else:
                    pass
                if k > time:
                    afterKey = k
                else:
                    pass
            beforeValue = timeSamples.get(beforeKey)
            afterValue = timeSamples.get(afterKey)
            if isinstance(beforeValue, (int, float,
                                        Gf.Vec2d, Gf.Vec2f, Gf.Vec2h, Gf.Vec2i,
                                        Gf.Vec3d, Gf.Vec3f, Gf.Vec3h, Gf.Vec3i,
                                        Gf.Vec4d, Gf.Vec4f, Gf.Vec4h, Gf.Vec4i, )):
                value = beforeValue + (afterValue - beforeValue) * ((time - beforeKey) / (afterKey - beforeKey))
            else:
                value = beforeValue
            return value

    def __init__(
            self,
            name='',
            defaultValue=None,
            parent=None,
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

        self._defaultValue = defaultValue
        self._value = defaultValue
        self._timeSamples = None
        self._connect = None

        self._valueOverride = False
        self._inheritValue = defaultValue
        self._inheritTimeSamples = None
        self._inheritConnect = None

        self._builtIn = builtIn
        self._visible = visible
        self._isCustom = custom

        self._paramWidgets = []

        self._signalConnected = False
        self._reConnectSignal()

    def addParamWidget(self, w):
        if w not in self._paramWidgets:
            self._paramWidgets.append(w)

    def removeParamWidget(self, w):
        self._paramWidgets.remove(w)

    def _breakSignal(self):
        if self._signalConnected:
            self._signalConnected = False
            self.valueChanged.disconnect(self._valueChanged)

    def _reConnectSignal(self):
        if not self._signalConnected:
            self._signalConnected = True
            self.valueChanged.connect(self._valueChanged)

    def _valueChanged(self, param):
        self._node._paramterValueChanged(param)

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

    def nodeItem(self):
        return self._node.item

    def stage(self):
        return self._node.item.scene().stage

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
                value = self.getIntervalValue(self._timeSamples, time)
                return value
    
    def getTimeSamples(self):
        return self._timeSamples

    # --------------------set value--------------------
    def _beforeSetValue(self):
        for w in self._paramWidgets:
            w._breakEditSignal()

    def _afterSetValue(self):
        for w in self._paramWidgets:
            w._reConnectEditSignal()

    def setHasKey(self, hasKey):
        if hasKey:
            if self._timeSamples is None:
                self._timeSamples = {}
        else:
            self._timeSamples = None

    def removeKey(self, time, emitSignal=True):
        self._beforeSetValue()
        time = float(time)
        if self.hasKey() and time in self._timeSamples.keys():
            self._timeSamples.pop(time)
            if len(self._timeSamples.keys()) == 0:
                self._timeSamples = None
            if emitSignal:
                self.valueChanged.emit(self)
        self._afterSetValue()

    def removeAllKeys(self, emitSignal=True):
        self.setTimeSamples(None, emitSignal)

    def setValue(self, value, emitSignal=True, override=True):
        self._beforeSetValue()
        self._valueOverride = override
        self._value = value
        if emitSignal:
            self.valueChanged.emit(self)
        self._afterSetValue()

    def setValueAt(self, value, time=None, emitSignal=True, override=True):
        self._valueOverride = override
        if self._timeSamples is None:
            self.setValue(value, emitSignal, override=override)
            return

        self._beforeSetValue()
        self._timeSamples.update({time: value})
        if emitSignal:
            self.valueChanged.emit(self)
        self._afterSetValue()

    def setTimeSamples(self, timeSamples, emitSignal=True, override=True):
        self._beforeSetValue()
        self._valueOverride = override
        self._timeSamples = timeSamples
        if emitSignal:
            self.valueChanged.emit(self)
        self._afterSetValue()

    def setConnect(self, connect, emitSignal=True, override=True):
        self._beforeSetValue()
        self._valueOverride = override
        self._connect = connect
        if emitSignal:
            self.valueChanged.emit(self)
        self._afterSetValue()

    def setInheritValue(self, value):
        self._inheritValue = value

    def setInheritTimeSamples(self, timeSamples):
        self._inheritTimeSamples = timeSamples

    def setInheritConnect(self, connect):
        self._inheritConnect = connect

    def setTimeSamplesQuietly(self, timeSamples, **kwargs):
        self.setTimeSamples(timeSamples, emitSignal=False, **kwargs)

    def setValueQuietly(self, value, **kwargs):
        self.setValue(value, emitSignal=False, **kwargs)

    def setConnectQuietly(self, connect, **kwargs):
        self.setConnect(connect, emitSignal=False, **kwargs)

    def breakConnect(self):
        self._connect = None
        self.valueChanged.emit(self)

    def getShowValues(self):
        if self._valueOverride:
            return self.getValue(), self.getTimeSamples(), self.getConnect()
        else:
            return self._inheritValue, self._inheritTimeSamples, self._inheritConnect

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

    def setOverride(self, override):
        self._valueOverride = override
        self.valueChanged.emit(self)

    def isOverride(self):
        return self._valueOverride


