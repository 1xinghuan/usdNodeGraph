from usdNodeGraph.module.sqt import *
from ..param_widget import *
from usdNodeGraph.utils.res import resource
from usdNodeGraph.ui.utils.layout import FormLayout


class NodeParameterWidget(QWidget):
    removeClicked = Signal()

    def __init__(self):
        super(NodeParameterWidget, self).__init__()

        self._node = None
        self._tabs = {}
        self._paramWidgets = {}
        self._expanded = True

        self._initUI()
        self._createSignal()

    def _createSignal(self):
        self.expandButton.clicked.connect(self._expandClicked)
        self.closeButton.clicked.connect(self._closeClicked)

    def _initUI(self):

        self._backLabel = QLabel(parent=self)
        self._backLabel.move(0, 0)
        self._backLabel.setStyleSheet('''
        background: rgb(250, 250, 250, 10);
        border-radius: 3px;
        ''')

        self.masterLayout = QVBoxLayout()
        self.masterLayout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.masterLayout)

        self.expandButton = QPushButton()
        self.expandButton.setIcon(resource.get_qicon('btn', 'arrow1_down.png'))
        self.nodeNameEdit = StringParameterWidget()
        self.nodeTypeLabel = QLabel()
        self.closeButton = QPushButton()
        self.closeButton.setIcon(resource.get_qicon('btn', 'close.png'))

        self.expandButton.setFixedSize(20, 20)
        self.closeButton.setFixedSize(20, 20)
        self.nodeNameEdit.setFixedHeight(20)
        self.nodeTypeLabel.setFixedHeight(20)

        self.topLayout = QHBoxLayout()
        self.topLayout.addWidget(self.expandButton)
        self.topLayout.addWidget(self.nodeNameEdit)
        self.topLayout.addWidget(self.nodeTypeLabel)
        self.topLayout.addStretch()
        self.topLayout.addWidget(self.closeButton)

        self.parameterTabWidget = QTabWidget()

        self.masterLayout.addLayout(self.topLayout)
        self.masterLayout.addWidget(self.parameterTabWidget)

        self.setSizePolicy(QSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Maximum
        ))

    def sizeHint(self):
        return self.minimumSizeHint()

    def _expandClicked(self):
        self._expanded = not self._expanded
        self.parameterTabWidget.setVisible(self._expanded)
        if self._expanded:
            self.expandButton.setIcon(resource.get_qicon('btn', 'arrow1_down.png'))
        else:
            self.expandButton.setIcon(resource.get_qicon('btn', 'arrow1_right.png'))

    def _closeClicked(self):
        # self.deleteLater()
        self.removeClicked.emit()

    def resizeEvent(self, event):
        super(NodeParameterWidget, self).resizeEvent(event)

        self._backLabel.resize(self.width(), 30)

    def setNode(self, node):
        self._node = node
        self._node.nodeObject.parameterAdded.connect(self._nodeParameterAdded)
        self._node.nodeObject.parameterRemoved.connect(self._nodeParameterRemoved)

        self.nodeNameEdit.setParameter(node.parameter('name'))

        self._buildUI()
        self.updateUI()

    def getNode(self):
        return self._node

    def createParameterWidget(self, parameter, layout):
        if parameter.isVisible():
            parameterLabel = parameter.getLabel()
            # if len(parameterLabel) > 15:
            #     parameterLabel = '{}...{}'.format(parameterLabel[:6], parameterLabel[-6:])
            parameterWidget = ParameterObject.createParameterWidget(parameter)

            self._paramWidgets.update({parameter.name(): parameterWidget})
            layout.addRow(parameterLabel, parameterWidget)

    def _buildTab(self, label, parameters=[]):
        layout = FormLayout()
        layout.setLabelAlignment(Qt.AlignRight)
        tab = QWidget()
        tab.setLayout(layout)
        self._tabs.update({label: tab})

        for parameter in parameters:
            self.createParameterWidget(parameter, layout)

        self.parameterTabWidget.addTab(tab, label)

    def _buildUI(self):
        parameters = self._node.parameters()
        nodeParameters = [param for param in parameters if not param.isBuiltIn()]
        builtInParameters = [param for param in parameters if param.isBuiltIn() and param.name() != 'name']

        nodeParameters.sort(lambda p1, p2: cmp(p1.getOrder(), p2.getOrder()))
        builtInParameters.sort(lambda p1, p2: cmp(p1.getOrder(), p2.getOrder()))

        self._buildTab(self._node.nodeType, nodeParameters)
        self._buildTab('Node', builtInParameters)

    def updateUI(self):
        self.nodeTypeLabel.setText(self._node.nodeType)
        self.nodeNameEdit.setPyValue(self._node.name())

        for paramWidget in self._paramWidgets.values():
            if paramWidget is not None:
                paramWidget.updateUI()

    def _nodeParameterAdded(self, parameter):
        tab = self._tabs[self._node.nodeType]
        layout = tab.layout()
        self.createParameterWidget(parameter, layout)

    def _nodeParameterRemoved(self, parameterName):
        if parameterName in self._paramWidgets:
            parameterWidget = self._paramWidgets[parameterName]
            self._paramWidgets.pop(parameterName)
            layout = parameterWidget.parentLayout
            layout.removeRowWidget(parameterWidget)


class ParameterPanel(QWidget):
    def __init__(self, *args, **kwargs):
        super(ParameterPanel, self).__init__(*args, **kwargs)

        self._nodes = []
        self._widgets = []

        self._initUI()

        self.widgetNumEdit.editingFinished.connect(self._numChanged)
        self.clearButton.clicked.connect(self.clearAll)

    def _initUI(self):

        self.masterLayout = QVBoxLayout()
        self.setLayout(self.masterLayout)

        self.widgetNumEdit = QLineEdit('10')
        self.widgetNumEdit.setFixedSize(50, 20)
        self.clearButton = QPushButton()
        self.clearButton.setFixedSize(20, 20)
        self.clearButton.setIcon(resource.get_qicon('btn', 'close.png'))
        self.widgetsAreaWidget = QWidget()
        self.widgetsAreaLayout = QVBoxLayout()
        self.widgetsAreaLayout.setAlignment(Qt.AlignTop)
        self.widgetsAreaLayout.addStretch()
        self.widgetsAreaWidget.setLayout(self.widgetsAreaLayout)
        self.widgetsArea = QScrollArea()
        self.widgetsArea.setWidget(self.widgetsAreaWidget)
        self.widgetsArea.setWidgetResizable(True)

        self.topLayout = QHBoxLayout()
        # self.topLayout.setAlignment(Qt.AlignLeft)
        self.topLayout.addWidget(self.widgetNumEdit)
        self.topLayout.addWidget(self.clearButton)
        self.topLayout.addStretch()

        self.masterLayout.addLayout(self.topLayout)
        self.masterLayout.addWidget(self.widgetsArea)

    def sizeHint(self):
        return QSize(200, 200)

    def _numChanged(self):
        self._removeExtraWidgets()

    def _removeExtraWidgets(self):
        num = int(self.widgetNumEdit.text())
        indexs = range(len(self._widgets))
        indexs.sort(reverse=True)
        for i in indexs:
            if i + 1 > num:
                w = self._widgets[i]
                self._removeWidget(w)

    def _removeRequired(self):
        widget = self.sender()
        self._removeWidget(widget)

    def _removeWidget(self, nodeWidget):
        self._widgets.remove(nodeWidget)
        self._nodes.remove(nodeWidget.getNode())
        nodeWidget.deleteLater()

    def _removeNode(self, node):
        for w in self._widgets:
            if w.getNode() == node:
                self._removeWidget(w)

    def clearAll(self):
        for nodeWidget in self._widgets:
            self._nodes.remove(nodeWidget.getNode())
            nodeWidget.deleteLater()
        self._widgets = []

    def addNode(self, node):
        if node in self._nodes:
            self._removeNode(node)

        nodeParameterWidget = NodeParameterWidget()
        nodeParameterWidget.setNode(node)

        nodeParameterWidget.removeClicked.connect(self._removeRequired)

        self._widgets.insert(0, nodeParameterWidget)
        self._nodes.insert(0, node)

        self.widgetsAreaLayout.insertWidget(0, nodeParameterWidget)

        self._removeExtraWidgets()


