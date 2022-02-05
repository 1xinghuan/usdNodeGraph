# -*- coding: utf-8 -*-

import copy
import json
from pxr import Gf, Sdf
from usdNodeGraph.module.sqt import QtCore


class Parameter(QtCore.QObject):
    parameterTypeString = None
    parameterWidgetString = None
    valueTypeName = None
    valueDefault = None
    valueChanged = QtCore.Signal(object)

    _parametersMap = {}
    _parameterWidgetsMap = {}

    @classmethod
    def registerParameter(cls, parameterClass):
        typeName = parameterClass.parameterTypeString
        cls._parametersMap.update({
            typeName: parameterClass
        })

    @classmethod
    def registerParameterWidget(cls, typeName, parameterWidget):
        cls._parameterWidgetsMap.update({
            typeName: parameterWidget
        })

    @classmethod
    def getParameterTypes(cls):
        return list(cls._parametersMap.keys())

    @classmethod
    def getParameter(cls, typeName):
        return cls._parametersMap.get(typeName)

    @classmethod
    def getValueDefault(cls):
        return cls.valueDefault

    @classmethod
    def convertValueFromPy(cls, pyValue):
        if pyValue == 'Sdf.ValueBlock':
            return Sdf.ValueBlock()
        return cls._convertValueFromPy(pyValue)

    @classmethod
    def _convertValueFromPy(cls, pyValue):
        return pyValue

    @classmethod
    def convertValueToPy(cls, usdValue):
        if usdValue == Sdf.ValueBlock():
            return 'Sdf.ValueBlock'
        return cls._convertValueToPy(usdValue)

    @classmethod
    def _convertValueToPy(cls, usdValue):
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
        keys = list(timeSamples.keys())
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
                                        Gf.Vec4d, Gf.Vec4f, Gf.Vec4h, Gf.Vec4i,)):
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
            custom=False,
            hints=None,
            **kwargs
    ):
        super(Parameter, self).__init__()

        self._name = name
        self._label = name if label is None else label
        self._node = parent

        defaultValue = defaultValue if defaultValue is not None else self.getValueDefault()

        self._defaultValue = defaultValue
        self._overrideValue = defaultValue
        self._overrideTimeSamples = None
        self._overrideConnect = None

        self._valueOverride = False
        self._inheritValue = defaultValue
        self._inheritTimeSamples = None
        self._inheritConnect = None

        self._metadata = {}
        self._defaultMetadata = {}

        self._hints = {} if hints is None else hints
        self.initHints(self._hints)
        self._defaultHints = self._hints.copy()

        self._builtIn = builtIn
        self._visible = visible
        self._isCustom = custom

        self._paramWidgets = []

        self._signalConnected = False
        self._reConnectSignal()

    def initHints(self, hints):
        widget = hints.get('widget', '')
        if widget == '':
            hints['widget'] = self.parameterWidgetString

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
        return self.getTimeSamples() is not None

    def hasConnect(self):
        return self.getConnect() is not None

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

    def setVisible(self, visible):
        self._visible = visible

    def _getValue(self, _value, _timeSamples, time):
        if _timeSamples is None:
            return _value
        else:
            if time is None:
                return list(_timeSamples.values())[0]
            else:
                value = self.getIntervalValue(_timeSamples, time)
                return value

    def getInheritValue(self, time=None):
        return self._getValue(self._inheritValue, self._inheritTimeSamples, time)

    def getOverrideValue(self, time=None):
        return self._getValue(self._overrideValue, self._overrideTimeSamples, time)

    def getValue(self, time=None):
        if self._node.hasProperty(self._name):
            return self._node.getProperty(self._name)
        if self.isOverride():
            return self.getOverrideValue(time)
        else:
            return self.getInheritValue(time)

    def getPyValue(self):
        v = self.getValue()
        return self.convertValueToPy(v)

    def getInheritTimeSamples(self):
        return self._inheritTimeSamples

    def getOverrideTimeSamples(self):
        return self._overrideTimeSamples

    def getTimeSamples(self):
        return self._overrideTimeSamples if self.isOverride() else self._inheritTimeSamples

    def getInheritConnect(self):
        return self._inheritConnect

    def getOverrideConnect(self):
        return self._overrideConnect

    def getConnect(self):
        return self._overrideConnect if self.isOverride() else self._inheritConnect

    def hasMetadatas(self):
        return self._metadata != {}

    def hasMetadata(self, key):
        return key in self._metadata

    def getMetadataKyes(self):
        return list(self._metadata.keys())

    def getMetadataValue(self, key, default=None):
        strValue = self._metadata.get(key, default)
        try:
            value = eval(strValue)
        except:
            value = strValue
        return value

    def getMetadatas(self):
        return self._metadata

    def getDefaultMetadatas(self):
        return self._defaultMetadata

    def getMetadatasAsString(self):
        return json.dumps(self._metadata, indent=4)

    def hasHint(self, key):
        return key in self._hints

    def getHints(self):
        return self._hints

    def getDefaultHints(self):
        return self._defaultHints

    def getHintValue(self, key, defaultValue=None):
        strValue = self._hints.get(key, defaultValue)
        try:
            value = eval(strValue)
        except:
            value = strValue
        return value

    def getParameterWidgetClass(self):
        typeName = self.getHintValue('widget')
        widgetClass = self._parameterWidgetsMap.get(typeName)
        return widgetClass

    # --------------------set value--------------------
    def setMetadata(self, key, value):
        if key == 'custom' and value in [False, 'False']:
            return
        if key == 'variability' and value in [Sdf.VariabilityVarying, 'Sdf.VariabilityVarying']:
            return
        self._metadata[key] = str(value)

    def setHint(self, key, value):
        self._hints[key] = str(value)

    def _beforeSetValue(self):
        for w in self._paramWidgets:
            w._breakEditSignal()

    def _afterSetValue(self):
        for w in self._paramWidgets:
            w._reConnectEditSignal()

    def setHasKey(self, hasKey):
        if hasKey:
            if self._overrideTimeSamples is None:
                self._overrideTimeSamples = {}
        else:
            self._overrideTimeSamples = None

    def removeKey(self, time, emitSignal=True):
        self._beforeSetValue()
        time = float(time)
        if self.hasKey() and time in self._overrideTimeSamples.keys():
            self._overrideTimeSamples.pop(time)
            if len(list(self._overrideTimeSamples.keys())) == 0:
                self._overrideTimeSamples = None
            if emitSignal:
                self.valueChanged.emit(self)
        self._afterSetValue()

    def removeAllKeys(self, emitSignal=True):
        self.setTimeSamples(None, emitSignal)

    def setValue(self, value, emitSignal=True, override=True):
        self._beforeSetValue()
        self._valueOverride = override
        self._overrideValue = value
        if emitSignal:
            self.valueChanged.emit(self)
        self._afterSetValue()

    def setValueAt(self, value, time=None, emitSignal=True, override=True):
        self._valueOverride = override
        if self._overrideTimeSamples is None:
            self.setValue(value, emitSignal, override=override)
            return

        self._beforeSetValue()
        self._overrideTimeSamples.update({time: value})
        if emitSignal:
            self.valueChanged.emit(self)
        self._afterSetValue()

    def setTimeSamples(self, timeSamples, emitSignal=True, override=True):
        self._beforeSetValue()
        self._valueOverride = override
        self._overrideTimeSamples = timeSamples
        if emitSignal:
            self.valueChanged.emit(self)
        self._afterSetValue()

    def setConnect(self, connect, emitSignal=True, override=True):
        self._beforeSetValue()
        self._valueOverride = override
        self._overrideConnect = connect
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
        self._overrideConnect = None
        self.valueChanged.emit(self)

    def getShowValues(self):
        if self._valueOverride:
            return self.getValue(), self.getTimeSamples(), self.getConnect()
        else:
            return self._inheritValue, self._inheritTimeSamples, self._inheritConnect

    def isCustom(self):
        if self._isCustom in [True, 'True', '1']:
            return True
        return False

    def setLabel(self, label):
        self._label = label

    def getLabel(self):
        return self._label

    def setOverride(self, override):
        self._valueOverride = override
        self.valueChanged.emit(self)

    def isOverride(self):
        return self._valueOverride

    def toXmlElement(self):
        from usdNodeGraph.core.parse._xml import ET

        custom = self.isCustom()
        builtIn = self.isBuiltIn()
        visible = self.isVisible()

        timeSamplesDict = None
        value = None
        connect = None

        if self.hasConnect():
            connect = self.getConnect()
        if self.hasKey():
            timeSamples = self.getTimeSamples()
            timeSamplesDict = {}
            for t, v in timeSamples.items():
                timeSamplesDict.update({t: self.convertValueToPy(v)})
        else:
            value = self.convertValueToPy(self.getValue())

        paramElement = ET.Element('p')
        paramElement.set('n', self.name())

        if not builtIn:
            paramElement.set('t', self.parameterTypeString)
            if not visible:
                paramElement.set('vis', '0')
        if custom:
            paramElement.set('cus', str(custom))
        paramElement.set('val', str(value))
        if connect is not None:
            paramElement.set('con', connect)
        if timeSamplesDict is not None:
            for t, v in timeSamplesDict.items():
                sample = ET.Element('s')
                sample.set('t', str(t))
                sample.set('v', str(v))
                paramElement.append(sample)

        for key, value in self.getMetadatas().items():
            if key in self.getDefaultMetadatas() and value == self.getDefaultMetadatas().get(key):
                continue
            metadataElement = ET.Element('m')
            metadataElement.set('k', key)
            metadataElement.set('v', value)
            paramElement.append(metadataElement)

        for key, value in self.getHints().items():
            if key in self.getDefaultHints() and value == self.getDefaultHints().get(key):
                continue
            hintElement = ET.Element('h')
            hintElement.set('k', str(key))
            hintElement.set('v', str(value))
            paramElement.append(hintElement)

        return paramElement

    def toXml(self):
        from usdNodeGraph.core.parse._xml import convertToString

        element = self.toXmlElement()
        return convertToString(element)

