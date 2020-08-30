from usdNodeGraph.module.sqt import *
from usdNodeGraph.core.parameter import Parameter
from usdNodeGraph.utils.res import resource
from usdNodeGraph.core.state.core import GraphState
from usdNodeGraph.ui.utils.layout import clearLayout
from usdNodeGraph.utils.log import get_logger
from usdNodeGraph.ui.utils.log import LogWindow
from ..param_edit.number_edit import IntEditWidget, FloatEditWidget

logger = get_logger('usdNodeGraph.ParameterWidget')


class ParameterWidget(object):
    parameterClass = None
    editValueChanged = QtCore.Signal()

    @classmethod
    def createParameterWidget(cls, parameter):
        typeName = parameter.parameterTypeString
        parameterWidgetClass = Parameter.getParameterWidget(typeName)

        if parameterWidgetClass is None:
            message = 'Un-Support Attribute Type in createParameterWidget! {}'.format(typeName)
            LogWindow.warning(message)
            logger.warning(message)
            return

        parameterWidget = parameterWidgetClass()
        parameterWidget.setParameter(parameter)

        return parameterWidget

    def __init__(self):
        super(ParameterWidget, self).__init__()

        self._parameter = None
        self._signalBreaked = True
        self._editSignalBreaked = True

        # self.masterLayout = None
        self._connectEdit = None

        self._editSignalBreaked = False
        self.editValueChanged.connect(self._editWidgetValueChanged)

    def _getStage(self):
        stage = self._parameter.node().getStage()
        return stage

    def _getCurrentTime(self):
        return GraphState.getCurrentTime(self._getStage())

    def _editWidgetValueChanged(self):
        self._setValueFromEdit()

    def _breakEditSignal(self):
        if not self._editSignalBreaked:
            self._editSignalBreaked = True
            self.editValueChanged.disconnect(self._editWidgetValueChanged)

    def _reConnectEditSignal(self):
        if self._editSignalBreaked:
            self._editSignalBreaked = False
            self.editValueChanged.connect(self._editWidgetValueChanged)

    def _breakSignal(self):
        if not self._signalBreaked:
            self._signalBreaked = True
            self._parameter.valueChanged.disconnect(self._parameterValueChanged)
        # self._parameter._breakSignal()

    def _reConnectSignal(self):
        if self._signalBreaked:
            self._signalBreaked = False
            self._parameter.valueChanged.connect(self._parameterValueChanged)
        # self._parameter._reConnectSignal()

    def _parameterValueChanged(self, parameter):
        self.updateUI()

    def _setValueFromEdit(self):
        value = self.getPyValue()
        value = self._parameter.convertValueFromPy(value)

        self._breakSignal()
        self._parameter.setValueAt(value, self._getCurrentTime())
        self._reConnectSignal()

    def setParameter(self, parameter, update=False):
        self._parameter = parameter
        self._parameter.addParamWidget(self)
        self._reConnectSignal()
        if update:
            self.updateUI()

    def getParameter(self):
        return self._parameter

    def _setMasterWidgetEnable(self, enable):
        pass

    def _beforeUpdateUI(self):
        self._breakEditSignal()
        self._breakSignal()

    def _afterUpdateUI(self):
        self._reConnectEditSignal()
        self._reConnectSignal()

    def updateUI(self):
        self._beforeUpdateUI()
        self._updateUI()
        self._afterUpdateUI()

    def _updateUI(self):
        self.setToolTip(self._parameter.name())

        value, timeSamples, connect = self._parameter.getShowValues()
        hasConnect = connect is not None

        if hasConnect:
            if self._connectEdit is None:
                self._connectEdit = QtWidgets.QLineEdit()
                self._connectEdit.setStyleSheet('QLineEdit{background: rgb(60, 60, 70)}')
                self._connectEdit.setReadOnly(True)
                self.masterLayout.addWidget(self._connectEdit)

                # self._connectEdit.editingFinished.connect(self._connectEditChanged)

            self._connectEdit.setText(self._parameter.getConnect())

        self._setMasterWidgetEnable(not hasConnect)
        if self._connectEdit is not None:
            self._connectEdit.setVisible(hasConnect)

        if timeSamples is not None:
            timeSamples = self._parameter.convertTimeSamplesToPy(timeSamples)
            self.setPyTimeSamples(timeSamples)
        else:
            value = self._parameter.convertValueToPy(value)
            self.setPyValue(value)

    def _connectEditChanged(self):
        self._breakSignal()
        connect = str(self._connectEdit.text())
        self._parameter.setConnect(connect)
        self._reConnectSignal()


class ArrayParameterWidget(QtWidgets.QWidget, ParameterWidget):
    def __init__(self):
        super(ArrayParameterWidget, self).__init__()
        ParameterWidget.__init__(self)

        self.masterLayout = QtWidgets.QVBoxLayout()
        self.masterLayout.setContentsMargins(0, 0, 0, 0)
        self.masterLayout.setSpacing(0)
        self.setLayout(self.masterLayout)

        self.expandButton = QtWidgets.QPushButton('expand...')
        self.expandButton.setFixedHeight(20)
        self.expandButton.setSizePolicy(QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed
        ))

        self.scrollArea = QtWidgets.QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setMinimumHeight(100)
        self.scrollArea.setVisible(0)
        self.areaWidget = None
        self.areaLayout = None
        self.formLayout = None

        self.masterLayout.addWidget(self.expandButton)
        self.masterLayout.addWidget(self.scrollArea)

        self.editWidgets = []
        self.lineEdits = []
        self.expanded = 0

        self.expandButton.clicked.connect(self._expandClicked)

    def _setMasterWidgetEnable(self, enable):
        self.expandButton.setVisible(enable)
        self.scrollArea.setVisible(enable)

    def _getEditWidgetClass(self):
        return None

    def _getChildParamterClass(self):
        return None

    def _initArea(self):
        self.addButton = QtWidgets.QPushButton()
        self.addButton.setIcon(resource.get_qicon('btn', 'add_white.png'))
        self.addButton.setFixedSize(20, 20)

        self.areaWidget = QtWidgets.QWidget()
        self.areaLayout = QtWidgets.QVBoxLayout()
        self.buttonLayout = QtWidgets.QHBoxLayout()
        self.buttonLayout.addWidget(self.addButton)
        self.buttonLayout.setAlignment(QtCore.Qt.AlignRight)

        self.formLayout = QtWidgets.QFormLayout()
        self.areaLayout.addLayout(self.formLayout)
        self.areaLayout.addLayout(self.buttonLayout)
        self.areaWidget.setLayout(self.areaLayout)
        self.scrollArea.setWidget(self.areaWidget)

        self.addButton.clicked.connect(self._addClicked)

    def _addClicked(self):
        pass

    def _expandClicked(self):
        self.expanded = 1 - self.expanded
        if self.areaWidget is None:
            self._initArea()
        self.scrollArea.setVisible(self.expanded)
        self.expandButton.setFixedHeight(7 if self.expanded else 20)
        self.updateUI()

    def addEditWidget(self, index, pyValue=None, pyTimeSamples=None):
        editWidgetClass = self._getEditWidgetClass()
        editWidget = editWidgetClass()
        editWidget.parameterWidget = self

        if pyTimeSamples is None:
            editWidget.setPyValue(pyValue)
        else:
            editWidget.setPyTimeSamples(pyTimeSamples)

        editWidget.editValueChanged.connect(self._editValueChanged)

        self.editWidgets.append(editWidget)
        self.formLayout.addRow(str(index), editWidget)

    def _updateUI(self):
        self.setToolTip(self._parameter.name())
        text = 'expand...{}'.format(len(self._parameter.getValue()))
        self.expandButton.setText(text)
        self.expandButton.setToolTip(text)

        if self.formLayout is not None and self.scrollArea.isVisible():
            clearLayout(self.formLayout)
            self.editWidgets = []

            timeSamples = self._parameter.getTimeSamples()
            if timeSamples is not None:
                timeSamples = self._parameter.convertTimeSamplesToPy(timeSamples)

                valueNum = len(timeSamples.values()[0])

                for index in range(valueNum):
                    indexPyTimeSamples = {}
                    for t, v in timeSamples.items():
                        indexPyTimeSamples[t] = v[index]
                    self.addEditWidget(index, pyTimeSamples=indexPyTimeSamples)
            else:
                value = self._parameter.getValue()
                value = self._parameter.convertValueToPy(value)

                for index, v in enumerate(value):
                    self.addEditWidget(index, pyValue=v)

    def _editValueChanged(self):
        value = [edit.getPyValue() for edit in self.editWidgets]
        value = self._parameter.convertValueFromPy(value)

        self._breakSignal()
        self._parameter.setValueAt(value, self._getCurrentTime())
        self._reConnectSignal()


class BasicWidget(object):
    def __init__(self):
        super(BasicWidget, self).__init__()

        self._isNumber = True
        self._hasKey = False
        self._keys = {}

    def hasKeys(self):
        return self._hasKey

    def setKey(self, value, time):
        if not isinstance(value, (int, float)):
            self._isNumber = False
        self._hasKey = True
        self._keys[float(time)] = value
        self.updateUI(time)

    def setValue(self, value):
        pass

    def removeKey(self, time):
        self._keys.pop(float(time))

    def reset(self):
        self.removeAllKeys()

    def removeAllKeys(self):
        self._hasKey = False
        self._keys = {}

    def getKeys(self):
        return self._keys

    def getValueAt(self, time):
        if time in self._keys:
            value = self._keys.get(float(time))
        else:
            value = Parameter.getIntervalValue(self._keys, time)
        return value


class BasicLineEdit(QtWidgets.QLineEdit, BasicWidget):
    def __init__(self):
        super(BasicLineEdit, self).__init__()
        BasicWidget.__init__(self)

        self._editWidget = None
        self._editMode = False
        self._editStartPos = None

    def setValue(self, value):
        self.removeAllKeys()
        self.setText(str(value))
        self.updateUI()

    def setText(self, string):
        super(BasicLineEdit, self).setText(string)
        self.setCursorPosition(0)

    def updateUI(self, time=0):
        if self._hasKey:
            value = self.getValueAt(time)
            self.setText(str(value))
            if time in self._keys:
                self.setStyleSheet('QLineEdit{background: rgb(50, 50, 100)}')
            else:
                self.setStyleSheet('QLineEdit{background: rgb(60, 60, 70)}')
        else:
            self.setStyleSheet('QLineEdit{background: transparent}')
            self.setReadOnly(False)

    def getRealValue(self):
        text = str(self.text())
        validator = self.validator()
        if validator is None:
            value = text
        elif isinstance(validator, QtGui.QIntValidator):
            try:  # may be ''
                value = int(text)
            except:
                value = 0
        else:
            try:  # may be ''
                value = float(text)
            except:
                value = 0
        return value

    def mousePressEvent(self, event):
        super(BasicLineEdit, self).mousePressEvent(event)
        if event.button() == QtCore.Qt.MiddleButton:
            self._enableEditMode()
            self._editStartPos = QtGui.QCursor.pos()

    def mouseReleaseEvent(self, event):
        super(BasicLineEdit, self).mouseReleaseEvent(event)
        if event.button() == QtCore.Qt.MiddleButton:
            self._disableEditMode()

    def mouseMoveEvent(self, event):
        super(BasicLineEdit, self).mouseMoveEvent(event)
        if self._editMode:
            targetPos = QtGui.QCursor.pos()
            QtGui.QCursor.setPos(self._editStartPos.x(), targetPos.y())
            value = self._editWidget.setEditingPos(targetPos - self._editStartPos)
            currentValue = self.getRealValue()
            self.setText(str(currentValue + value))
            self.editingFinished.emit()

    def _enableEditMode(self):
        from usdNodeGraph.ui.nodeGraph import USD_NODE_GRAPH_WINDOW

        pos = USD_NODE_GRAPH_WINDOW.mapFromGlobal(QtGui.QCursor.pos())
        x = pos.x() - self._editWidget.width() / 2
        y = pos.y() - self._editWidget.height() / 2
        self._editWidget.move(x, y)
        self._editWidget.setVisible(True)

        self._editMode = True

    def _disableEditMode(self):
        self._editMode = False
        if self._editWidget is not None:
            self._editWidget.setVisible(False)


class IntLineEdit(BasicLineEdit):
    def __init__(self):
        super(IntLineEdit, self).__init__()

        validator = QtGui.QIntValidator()
        self.setValidator(validator)

    def _enableEditMode(self):
        if self._editWidget is None:
            from usdNodeGraph.ui.nodeGraph import USD_NODE_GRAPH_WINDOW
            self._editWidget = IntEditWidget(parent=USD_NODE_GRAPH_WINDOW)
            self._editWidget.show()
        super(IntLineEdit, self)._enableEditMode()


class FloatLineEdit(BasicLineEdit):
    def __init__(self):
        super(FloatLineEdit, self).__init__()

        validator = QtGui.QDoubleValidator()
        self.setValidator(validator)

    def _enableEditMode(self):
        if self._editWidget is None:
            from usdNodeGraph.ui.nodeGraph import USD_NODE_GRAPH_WINDOW
            self._editWidget = FloatEditWidget(parent=USD_NODE_GRAPH_WINDOW)
            self._editWidget.show()
        super(FloatLineEdit, self)._enableEditMode()


class VecWidget(QtWidgets.QWidget):
    editValueChanged = QtCore.Signal()
    _valueSize = 1
    _lineEdit = BasicLineEdit

    def __init__(self):
        super(VecWidget, self).__init__()

        self.initUI()

    def initUI(self):
        self.masterLayout = QtWidgets.QHBoxLayout()
        self.masterLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.masterLayout)

        self.lineEdits = []
        for i in range(self._valueSize):
            lineEdit = self._lineEdit()

            # lineEdit.returnPressed.connect(self._editTextChanged)
            lineEdit.editingFinished.connect(self._editTextChanged)
            # lineEdit.textChanged.connect(self._editTextChanged)

            self.masterLayout.addWidget(lineEdit)
            self.lineEdits.append(lineEdit)

        GraphState.getState().currentTimeChanged.connect(self.updateLineEditsUI)

    def _editTextChanged(self):
        lineEdit = self.sender()
        if lineEdit.hasKeys():
            if hasattr(self, '_getStage'):
                stage = self._getStage()
            else:
                stage = self.parameterWidget._getStage()
            if hasattr(self, '_getCurrentTime'):
                time = self._getCurrentTime()
            else:
                time = self.parameterWidget._getCurrentTime()
            lineEdit.setKey(lineEdit.getRealValue(), time)

        self.editValueChanged.emit()

    def _setMasterWidgetEnable(self, enable):
        for i in self.lineEdits:
            i.setVisible(enable)

    def setPyValue(self, value):
        if not isinstance(value, list):
            value = [value]
        for index, v in enumerate(value):
            lineEdit = self.lineEdits[index]
            lineEdit.setValue(v)

    def getPyValue(self):
        value = []
        for edit in self.lineEdits:
            num = edit.getRealValue()
            value.append(num)

        if len(value) == 1:
            value = value[0]
        return value

    def _beforeSetPyTimeSamples(self):
        for lineEdit in self.lineEdits:
            lineEdit.reset()

    def setPyTimeSamples(self, timeSamples):
        self._beforeSetPyTimeSamples()
        self._setPyTimeSamples(timeSamples)
        self._afterSetPyTimeSamples()

    def _setPyTimeSamples(self, timeSamples):
        for time, value in timeSamples.items():
            if self._valueSize == 1:
                self.lineEdits[0].setKey(value, time)
            else:
                for index, lineEdit in enumerate(self.lineEdits):
                    lineEdit.setKey(value[index], time)

    def _afterSetPyTimeSamples(self):
        if hasattr(self, '_getCurrentTime'):
            time = self._getCurrentTime()
        else:
            time = self.parameterWidget._getCurrentTime()
        self.updateLineEditsUI(time)

    # def getPyTimeSamples(self):
    #     timeSamples = {}
    #
    #     return timeSamples

    def updateLineEditsUI(self, time=0):
        for lineEdit in self.lineEdits:
            lineEdit.updateUI(time=time)


class MatrixWidget(VecWidget):
    def initUI(self):
        self.masterLayout = QtWidgets.QVBoxLayout()
        self.masterLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.masterLayout)

        self.lineEdits = []
        for i in range(self._valueSize):
            layout = QtWidgets.QHBoxLayout()
            for j in range(self._valueSize):
                lineEdit = self._lineEdit()
                lineEdit.editingFinished.connect(self._editTextChanged)
                self.lineEdits.append(lineEdit)

                layout.addWidget(lineEdit)

            self.masterLayout.addLayout(layout)

        GraphState.getState().currentTimeChanged.connect(self.updateLineEditsUI)

    def setPyValue(self, value):
        if not isinstance(value, list):
            value = [value]
        for i, vec in enumerate(value):
            for j, v in enumerate(vec):
                index = i * self._valueSize + j
                lineEdit = self.lineEdits[index]
                lineEdit.setValue(v)

    def getPyValue(self):
        value = [[] for i in range(self._valueSize)]
        for index, edit in enumerate(self.lineEdits):
            i = index / self._valueSize
            j = index % self._valueSize

            num = edit.getRealValue()
            value[i].append(num)

        return value

    def _setPyTimeSamples(self, timeSamples):
        for time, value in timeSamples.items():
            for i, vec in enumerate(value):
                for j, v in enumerate(vec):
                    index = i * self._valueSize + j
                    lineEdit = self.lineEdits[index]
                    lineEdit.setKey(v, time)

