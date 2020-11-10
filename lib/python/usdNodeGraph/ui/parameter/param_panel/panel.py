from ..param_widget import *
from usdNodeGraph.utils.res import resource
from usdNodeGraph.ui.utils.layout import FormLayout
from usdNodeGraph.core.state.core import GraphState
from .metadata import MetadataPanel


CONTEXT_MENU = None


class ParamStatusButton(QtWidgets.QLabel):
    buttonClicked = QtCore.Signal()

    def __init__(self):
        super(ParamStatusButton, self).__init__()

        self._parameter = None
        size = 18

        self.defaultPixmap = resource.get_pixmap('btn', 'radio_unchecked.png', scale=size)
        self.overridePixmap = resource.get_pixmap('btn', 'radio_checked.png', scale=size)

        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setFixedSize(size, size)

        # self.buttonClicked.connect(self._selfClicked)

    def setParameter(self, parameter):
        self._parameter = parameter
        self._parameter.valueChanged.connect(self._valueChanged)
        self._updateColor()

    def _selfClicked(self):
        self._parameter.setOverride(not self._parameter.isOverride())

    def _valueChanged(self, *args, **kwargs):
        self._updateColor()

    def _updateColor(self):
        override = self._parameter.isOverride()
        if override:
            self.setPixmap(self.overridePixmap)
        else:
            self.setPixmap(self.defaultPixmap)

    def mouseReleaseEvent(self, event):
        self.buttonClicked.emit()
        self._selfClicked()


class ParamHelpLabel(QtWidgets.QLabel):
    def __init__(self):
        super(ParamHelpLabel, self).__init__()
        size = 16
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setFixedSize(size, size)
        self.setPixmap(resource.get_pixmap('btn', 'help.png', scale=size))
        self.setStyleSheet("""
        QToolTip{
            border: 1px solid gray;
        }
        """)

    def setParameter(self, param):
        help = param.getHintValue('help', '')
        self.setToolTip(help)


class ParamLabelWidget(QtWidgets.QWidget):
    paramLabelClicked = QtCore.Signal(object)

    def __init__(self):
        super(ParamLabelWidget, self).__init__()

        self._parameter = None

        self.masterLayout = QtWidgets.QHBoxLayout()
        self.masterLayout.setAlignment(QtCore.Qt.AlignLeft)
        self.masterLayout.setContentsMargins(0, 0, 0, 0)
        self.masterLayout.setSpacing(0)
        self.setLayout(self.masterLayout)

        self.nameLabel = QtWidgets.QLabel()
        self.statusLabel = ParamStatusButton()
        self.helpLabel = ParamHelpLabel()

        self.masterLayout.addWidget(self.nameLabel)
        self.masterLayout.addWidget(self.statusLabel)
        self.masterLayout.addWidget(self.helpLabel)

    def setParameter(self, parameter):
        self._parameter = parameter
        self.statusLabel.setParameter(parameter)
        self.helpLabel.setParameter(parameter)
        self.updateUI()

    def updateUI(self):
        self.nameLabel.setText(self._parameter.getLabel())
        tooltip = '{} {}'.format(self._parameter.parameterTypeString, self._parameter.name())
        self.nameLabel.setToolTip(tooltip)
        self.statusLabel._updateColor()

    def setContextMenu(self):
        self._context_menus = [
            ['Add Keyframe', self._addKeyframeClicked],
            ['Remove Keyframe', self._removeKeyframeClicked],
            ['Remove All Keys', self._removeAllKeysClicked],
        ]

    def _createContextMenu(self):
        self.setContextMenu()
        self.menu = QtWidgets.QMenu(self)
        for i in self._context_menus:
            action = QtWidgets.QAction(i[0], self.menu)
            action.triggered.connect(i[1])
            self.menu.addAction(action)

    def contextMenuEvent(self, event):
        super(ParamLabelWidget, self).contextMenuEvent(event)
        self._createContextMenu()
        self.menu.move(QtGui.QCursor().pos())
        self.menu.show()

        global CONTEXT_MENU
        CONTEXT_MENU = self.menu

    def _addKeyframeClicked(self):
        currentTime = GraphState.getCurrentTime(self._parameter.stage())
        currentValue = self._parameter.getValue(time=currentTime)
        self._parameter.setHasKey(True)
        self._parameter.setValueAt(currentValue, currentTime)

    def _removeKeyframeClicked(self):
        currentTime = GraphState.getCurrentTime(self._parameter.stage())
        self._parameter.removeKey(currentTime)

    def _removeAllKeysClicked(self):
        currentTime = GraphState.getCurrentTime(self._parameter.stage())
        currentValue = self._parameter.getValue(time=currentTime)
        self._parameter.removeAllKeys(emitSignal=False)
        self._parameter.setValue(currentValue)

    def mouseReleaseEvent(self, event):
        super(ParamLabelWidget, self).mouseReleaseEvent(event)
        self.paramLabelClicked.emit(self._parameter)


class PageWidget(QtWidgets.QWidget):
    def __init__(self, page):
        super(PageWidget, self).__init__()

        self._expand = 1
        self._page = page
        self._subPages = {}

        self.expandIcon = resource.get_qicon('btn', 'arrow1_down.png')
        self.unexpandIcon = resource.get_qicon('btn', 'arrow1_right.png')

        self.masterLayout = QtWidgets.QVBoxLayout()
        self.masterLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.masterLayout)

        self.upLayout = QtWidgets.QHBoxLayout()
        self.downLauout = QtWidgets.QVBoxLayout()
        self.downLauout.setContentsMargins(20, 0, 0, 0)
        self.downWidget = QtWidgets.QWidget()
        self.downWidget.setLayout(self.downLauout)
        self.formLayout = FormLayout()
        self.formLayout.setLabelAlignment(QtCore.Qt.AlignRight)
        self.pagesLayout = QtWidgets.QVBoxLayout()
        self.masterLayout.addLayout(self.upLayout)
        self.masterLayout.addWidget(self.downWidget)
        self.downLauout.addLayout(self.formLayout)
        self.downLauout.addLayout(self.pagesLayout)
        setattr(self.masterLayout, 'formLayout', self.formLayout)
        setattr(self.masterLayout, 'pagesLayout', self.pagesLayout)

        self.expandButton = QtWidgets.QPushButton()
        self.expandButton.setIcon(self.expandIcon)
        self.expandButton.setFixedSize(15, 15)
        self.expandButton.setStyleSheet('border:none')
        self.nameLabel = QtWidgets.QLabel(page.split('.')[-1])
        self.upLayout.addWidget(self.expandButton)
        self.upLayout.addWidget(self.nameLabel)

        self.expandButton.clicked.connect(self._expandClicked)

        self._expandClicked()

    def addPage(self, widget):
        self.pagesLayout.addWidget(widget)
        self._subPages.update({widget._page: widget})

    def findPage(self, subpage):
        if subpage not in self._subPages:
            pageWidget = PageWidget(subpage)
            self.addPage(pageWidget)
        return self._subPages[subpage]

    def _expandClicked(self):
        self._expand = 1 - self._expand
        self.downWidget.setVisible(self._expand)
        self.expandButton.setIcon(self.expandIcon if self._expand else self.unexpandIcon)


class NodeParameterWidget(QtWidgets.QFrame):
    removeClicked = QtCore.Signal()

    def __init__(self):
        super(NodeParameterWidget, self).__init__()

        self._nodeItem = None
        self._tabs = {}
        self._paramWidgets = {}
        self._paramLabelWidgets = {}
        self._pageWidgets = {}
        self._expanded = True
        self._isParamLabelClicked = False

        self._initUI()
        self._createSignal()

    def _createSignal(self):
        self.expandButton.clicked.connect(self._expandClicked)
        self.closeButton.clicked.connect(self._closeClicked)
        self.syncButton.clicked.connect(self._syncClicked)
        self.pushButton.clicked.connect(self._applyClicked)

    def _initUI(self):
        self.setObjectName('NodeParameterWidget')

        self._backLabel = QtWidgets.QLabel(parent=self)
        self._backLabel.move(0, 0)
        self._backLabel.setStyleSheet('''
        QLabel{
            background: rgb(250, 250, 250, 10);
            border-radius: 3px;
        }
        ''')
        self.setStyleSheet('''
        QFrame#NodeParameterWidget{
            border: 1px solid gray;
            border-radius: 3px;
        }
        ''')

        self.masterLayout = QtWidgets.QVBoxLayout()
        self.masterLayout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.masterLayout)

        self.expandButton = QtWidgets.QPushButton()
        self.expandButton.setIcon(resource.get_qicon('btn', 'arrow1_down.png'))
        self.nodeNameEdit = StringParameterWidget()
        self.nodeTypeLabel = QtWidgets.QLabel()
        self.nodePrimPathLabel = QtWidgets.QLineEdit()
        self.nodePrimPathLabel.setReadOnly(True)
        self.closeButton = QtWidgets.QPushButton()
        self.closeButton.setIcon(resource.get_qicon('btn', 'close.png'))

        self.syncButton = QtWidgets.QPushButton()
        self.syncButton.setIcon(resource.get_qicon('btn', 'refresh_blue.png'))
        self.syncButton.setToolTip('Sync To Parameter')
        self.pushButton = QtWidgets.QPushButton()
        self.pushButton.setIcon(resource.get_qicon('btn', 'arrow_up2_white.png'))
        self.pushButton.setToolTip('Force Apply Changes')

        for btn in [
            self.expandButton,
            self.closeButton,
            self.syncButton,
            self.pushButton,
        ]:
            btn.setFixedSize(20, 20)

        self.nodeNameEdit.setMaximumWidth(100)
        self.nodeNameEdit.setFixedHeight(20)
        self.nodeTypeLabel.setFixedHeight(20)
        self.nodePrimPathLabel.setFixedHeight(20)

        self.fillColorEdit = Color4fParameterWidget()
        self.borderColorEdit = Color4fParameterWidget()

        self.topLayout = QtWidgets.QHBoxLayout()
        self.topLayout.addWidget(self.expandButton)
        self.topLayout.addWidget(self.nodeNameEdit)
        self.topLayout.addWidget(self.nodeTypeLabel)
        self.topLayout.addWidget(self.nodePrimPathLabel)
        # self.topLayout.addStretch()
        # self.topLayout.addWidget(self.syncButton)
        self.topLayout.addWidget(self.fillColorEdit)
        self.topLayout.addWidget(self.borderColorEdit)
        self.topLayout.addWidget(self.pushButton)
        self.topLayout.addWidget(self.closeButton)

        self.parameterTabWidget = QtWidgets.QTabWidget()
        self.metadataWidget = MetadataPanel()
        self.metadataWidget.setVisible(False)

        self.downSplit = QtWidgets.QSplitter()
        # self.downSplit.setOrientation(QtCore.Qt.Vertical)
        self.downSplit.addWidget(self.parameterTabWidget)
        self.downSplit.addWidget(self.metadataWidget)

        self.masterLayout.addLayout(self.topLayout)
        self.masterLayout.addWidget(self.downSplit)

        self.setSizePolicy(QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred,
            QtWidgets.QSizePolicy.Maximum
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

    def _syncClicked(self):
        pass

    def _applyClicked(self):
        self._nodeItem.nodeObject.applyChanges()

    def resizeEvent(self, event):
        super(NodeParameterWidget, self).resizeEvent(event)

        self._backLabel.resize(self.width(), 30)

    def setNode(self, node):
        self._nodeItem = node
        self._nodeItem.panel = self
        self._nodeItem.nodeObject.parameterAdded.connect(self._nodeParameterAdded)
        self._nodeItem.nodeObject.parameterRemoved.connect(self._nodeParameterRemoved)
        self._nodeItem.nodeObject.parameterPagesCleared.connect(self._nodeParameterPagesCleared)

        self.nodeNameEdit.setParameter(node.parameter('name'))
        self.fillColorEdit.setParameter(node.parameter('fillColor'))
        self.borderColorEdit.setParameter(node.parameter('borderColor'))

        self._paramWidgets.update({'name': self.nodeNameEdit})
        self._paramWidgets.update({'fillColor': self.fillColorEdit})
        self._paramWidgets.update({'borderColor': self.borderColorEdit})

        self._buildUI()
        self.updateUI()

    def getNode(self):
        return self._nodeItem

    def createPageWidget(self, page, parentLayout):
        pageWidget = PageWidget(page)
        parentLayout.pagesLayout.addWidget(pageWidget)
        return pageWidget

    def findPageWidget(self, mainPage, parentLayout):
        if mainPage not in self._pageWidgets:
            mainPageWidget = self.createPageWidget(mainPage, parentLayout)
            self._pageWidgets[mainPage] = mainPageWidget

        return self._pageWidgets[mainPage]

    def findPageLayout(self, page, parentLayout):
        pages = page.split('.')
        mainPage = pages[0]
        currentWidget = self.findPageWidget(mainPage, parentLayout)
        for i in pages[1:]:
            currentWidget = currentWidget.findPage(i)
        layout = currentWidget.masterLayout
        return layout

    def createParameterWidget(self, parameter, layout):
        if not parameter.isVisible():
            return
        parameterLabel = ParamLabelWidget()
        parameterLabel.setParameter(parameter)
        parameterLabel.paramLabelClicked.connect(self._paramLabelClicked)
        parameterWidget = ParameterWidget.createParameterWidget(parameter)
        if parameterWidget is None:
            return

        self._paramWidgets.update({parameter.name(): parameterWidget})
        self._paramLabelWidgets.update({parameter.name(): parameterLabel})

        page = parameter.getHintValue('page', '')
        if page != '':
            layout = self.findPageLayout(page, layout)

        layout.formLayout.addRow(parameterLabel, parameterWidget)

    def removeParameterConnections(self):
        for paramName, widget in self._paramWidgets.items():
            param = self._nodeItem.parameter(paramName)
            param.removeParamWidget(widget)

    def _buildTab(self, label, parameters=[]):
        layout = QtWidgets.QVBoxLayout()
        formLayout = FormLayout()
        formLayout.setLabelAlignment(QtCore.Qt.AlignRight)
        pagesLayout = QtWidgets.QVBoxLayout()
        layout.addLayout(formLayout)
        layout.addLayout(pagesLayout)
        setattr(layout, 'formLayout', formLayout)
        setattr(layout, 'pagesLayout', pagesLayout)

        tab = QtWidgets.QWidget()
        tab.setLayout(layout)
        self._tabs.update({label: tab})

        for parameter in parameters:
            self.createParameterWidget(parameter, layout)

        self.parameterTabWidget.addTab(tab, label)

    def _buildUI(self):
        parameters = self._nodeItem.parameters()
        noTabParams = [param for param in parameters if not param.hasHint('tab')]
        nodeTabParams = [param for param in parameters if param.getHintValue('tab') == 'Node']

        self._buildTab(self._nodeItem.nodeType, noTabParams)
        self._buildTab('Node', nodeTabParams)

    def updateUI(self):
        self.nodeTypeLabel.setText(self._nodeItem.nodeType)
        self.nodePrimPathLabel.setText(':'.join(self._nodeItem.getPrimPath()))
        self.nodePrimPathLabel.setToolTip('\n'.join(self._nodeItem.getPrimPath()))

        for labelWidget in self._paramLabelWidgets.values():
            if labelWidget is not None:
                labelWidget.updateUI()
        for paramWidget in self._paramWidgets.values():
            if paramWidget is not None:
                paramWidget.updateUI()

    def _nodeParameterAdded(self, parameter):
        tab = self._tabs[self._nodeItem.nodeType]
        layout = tab.layout()
        self.createParameterWidget(parameter, layout)

    def _nodeParameterRemoved(self, parameterName):
        if parameterName in self._paramWidgets:
            parameterWidget = self._paramWidgets[parameterName]
            self._paramWidgets.pop(parameterName)
            layout = parameterWidget.parentLayout
            layout.removeRowWidget(parameterWidget)

    def _nodeParameterPagesCleared(self):
        tab = self._tabs[self._nodeItem.nodeType]
        layout = tab.layout()
        pagesLayout = layout.pagesLayout
        clearLayout(pagesLayout)
        self._pageWidgets = {}

    def setContextMenu(self):
        self._context_menus = [
            # ['Add Parameter', self._addParameterClicked],
            ['View Metadata', self._viewMetadataClicked],
        ]

    def _createContextMenu(self):
        self.setContextMenu()
        self.menu = QtWidgets.QMenu(self)
        for i in self._context_menus:
            action = QtWidgets.QAction(i[0], self.menu)
            action.triggered.connect(i[1])
            self.menu.addAction(action)

    def contextMenuEvent(self, event):
        super(NodeParameterWidget, self).contextMenuEvent(event)
        global CONTEXT_MENU
        if CONTEXT_MENU is None:
            self._createContextMenu()
            self.menu.move(QtGui.QCursor().pos())
            self.menu.show()
        else:
            CONTEXT_MENU = None

    def _addParameterClicked(self):
        pass

    def _viewMetadataClicked(self):
        self._viewMetadata(self._nodeItem.nodeObject)

    def _viewMetadata(self, obj):
        self.metadataWidget.setVisible(True)
        self.metadataWidget.setNodeOrParam(obj)

    def viewMetadata(self, obj):
        if obj.hasMetadatas():
            self._viewMetadata(obj)
        else:
            self.metadataWidget.setVisible(False)

    def _paramLabelClicked(self, param):
        self._isParamLabelClicked = True
        self.viewMetadata(param)

    def mouseReleaseEvent(self, *args, **kwargs):
        super(NodeParameterWidget, self).mouseReleaseEvent(*args, **kwargs)
        if self._isParamLabelClicked:
            self._isParamLabelClicked = False
        else:
            self.viewMetadata(self._nodeItem.nodeObject)

    def deleteLater(self):
        self._nodeItem.panel = None
        super(NodeParameterWidget, self).deleteLater()


class ParameterPanel(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(ParameterPanel, self).__init__(*args, **kwargs)

        self._nodes = []
        self._widgets = []

        self._initUI()

        self.widgetNumEdit.editingFinished.connect(self._numChanged)
        self.clearButton.clicked.connect(self.clearAll)

    def _initUI(self):

        self.masterLayout = QtWidgets.QVBoxLayout()
        self.setLayout(self.masterLayout)

        self.widgetNumEdit = QtWidgets.QLineEdit('10')
        self.widgetNumEdit.setFixedSize(50, 20)
        self.clearButton = QtWidgets.QPushButton()
        self.clearButton.setFixedSize(20, 20)
        self.clearButton.setIcon(resource.get_qicon('btn', 'close.png'))
        self.widgetsAreaWidget = QtWidgets.QWidget()
        self.widgetsAreaLayout = QtWidgets.QVBoxLayout()
        self.widgetsAreaLayout.setAlignment(QtCore.Qt.AlignTop)
        self.widgetsAreaLayout.setContentsMargins(0, 0, 0, 0)
        self.widgetsAreaLayout.addStretch()
        self.widgetsAreaWidget.setLayout(self.widgetsAreaLayout)
        self.widgetsArea = QtWidgets.QScrollArea()
        self.widgetsArea.setWidget(self.widgetsAreaWidget)
        self.widgetsArea.setWidgetResizable(True)

        self.topLayout = QtWidgets.QHBoxLayout()
        # self.topLayout.setAlignment(QtCore.Qt.AlignLeft)
        self.topLayout.addWidget(self.widgetNumEdit)
        self.topLayout.addWidget(self.clearButton)
        self.topLayout.addStretch()

        self.masterLayout.addLayout(self.topLayout)
        self.masterLayout.addWidget(self.widgetsArea)

    def sizeHint(self):
        return QtCore.QSize(200, 200)

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
        nodeWidget.removeParameterConnections()
        self._widgets.remove(nodeWidget)
        self._nodes.remove(nodeWidget.getNode())
        nodeWidget.deleteLater()

    def removeNode(self, nodeName):
        for w in self._widgets:
            if w.getNode().name() == nodeName:
                self._removeWidget(w)

    def clearAll(self):
        nodes = [n.name() for n in self._nodes]
        for node in nodes:
            self.removeNode(node)

    def addNode(self, node):
        if node.name() in [n.name() for n in self._nodes]:
            self.removeNode(node.name())

        nodeParameterWidget = NodeParameterWidget()
        nodeParameterWidget.setNode(node)

        nodeParameterWidget.removeClicked.connect(self._removeRequired)

        self._widgets.insert(0, nodeParameterWidget)
        self._nodes.insert(0, node)

        self.widgetsAreaLayout.insertWidget(0, nodeParameterWidget)

        self._removeExtraWidgets()

