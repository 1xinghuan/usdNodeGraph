# -*- coding: utf-8 -*-

import os
from pxr import Usd
from usdNodeGraph.module.sqt import *
from usdNodeGraph.ui.graph.view import GraphicsSceneWidget, isEditable
from usdNodeGraph.ui.parameter.param_panel import ParameterPanel
from usdNodeGraph.core.state.core import GraphState
from usdNodeGraph.ui.other.timeSlider import TimeSliderWidget
from usdNodeGraph.utils.settings import User_Setting, read_setting, write_setting
from usdNodeGraph.utils.res import resource


USD_NODE_GRAPH_WINDOW = None


class ApplyButton(QtWidgets.QToolButton):
    def __init__(self):
        super(ApplyButton, self).__init__()

        self.setPopupMode(QtWidgets.QToolButton.MenuButtonPopup)
        # self.setPopupMode(QtWidgets.QToolButton.DelayedPopup)
        self.setArrowType(QtCore.Qt.NoArrow)
        self.setStyleSheet("""
        QToolButton{
            text-align: left;
        }
        QToolButton::menu-indicator{
            image: None;
        }
        """)

        self._menu = QtWidgets.QMenu()
        self.liveUpdateAction = QtWidgets.QAction('Live Update', self._menu)
        self._menu.addAction(self.liveUpdateAction)
        self.setMenu(self._menu)

        self.setFixedWidth(30)

        self._liveUpdateModeChanged(GraphState.isLiveUpdate())

        GraphState.getState().liveUpdateModeChanged.connect(self._liveUpdateModeChanged)
        self.liveUpdateAction.triggered.connect(self._liveUpdateActionTriggered)

    def _liveUpdateModeChanged(self, value):
        if value:
            self.setIcon(resource.get_qicon('btn', 'live_update.png'))
            self.setToolTip('Live Update')
            self.liveUpdateAction.setText('Disable Live Update')
        else:
            self.setIcon(resource.get_qicon('btn', 'arrow_up2_white.png'))
            self.setToolTip('Update Stage')
            self.liveUpdateAction.setText('Enable Live Update')

    def _liveUpdateActionTriggered(self):
        GraphState.setLiveUpdate(1 - GraphState.isLiveUpdate())


class DockWidget(QtWidgets.QDockWidget):
    maximizedRequired = QtCore.Signal()

    def __init__(self, title='', objName='', *args, **kwargs):
        super(DockWidget, self).__init__(*args, **kwargs)

        self.setObjectName(objName)
        self.setWindowTitle(title)

    def keyPressEvent(self, event):
        super(DockWidget, self).keyPressEvent(event)

        if event.key() == QtCore.Qt.Key_Space:
            self.maximizedRequired.emit()


class NodeGraphTab(QtWidgets.QTabWidget):
    def __init__(self, *args, **kwargs):
        super(NodeGraphTab, self).__init__(*args, **kwargs)

        self.setTabsClosable(True)
        self.setMovable(True)


class UsdNodeGraph(QtWidgets.QMainWindow):
    entityItemDoubleClicked = QtCore.Signal(object)
    currentSceneChanged = QtCore.Signal(object)
    mainWindowClosed = QtCore.Signal()
    _actionShortCutMap = {}
    _addedActions = []
    _addedWidgetClasses = []

    @classmethod
    def registerActionShortCut(cls, actionName, shortCut):
        cls._actionShortCutMap.update({
            actionName: shortCut
        })

    @classmethod
    def registerActions(cls, actionList):
        cls._addedActions = actionList

    @classmethod
    def registerDockWidget(cls, widgetClass, name, label):
        cls._addedWidgetClasses.append([
            widgetClass, name, label
        ])

    @classmethod
    def getInstance(cls):
        return USD_NODE_GRAPH_WINDOW

    def __init__(
            self, app='main',
            parent=None
    ):
        super(UsdNodeGraph, self).__init__(parent=parent)

        global USD_NODE_GRAPH_WINDOW
        USD_NODE_GRAPH_WINDOW = self

        from usdNodeGraph.ui.plugin import loadPlugins
        loadPlugins()

        self.app = app

        self.currentScene = None
        self._usdFile = None
        self.scenes = []
        self._docks = []
        self._maxDock = None

        self._initUI()
        self._createSignal()

    def _createSignal(self):
        self.applyButton.clicked.connect(self._applyActionTriggered)
        self.reloadButton.clicked.connect(self._reloadLayerActionTriggered)
        self.nodeGraphTab.tabCloseRequested.connect(self._tabCloseRequest)
        self.nodeGraphTab.currentChanged.connect(self._tabChanged)

        for dock in self._docks:
            dock.maximizedRequired.connect(self._dockMaxRequired)

    def _getMenuActions(self):
        actions = [
            ['File', [
                ['open_file', 'Open', 'Ctrl+O', self._openActionTriggered],
                ['reopen_file', 'ReOpen', None, self._reopenActionTriggered],
                ['reload_stage', 'Reload Stage', 'Alt+Shift+R', self._reloadStageActionTriggered],
                ['reload_layer', 'Reload Layer', 'Alt+R', self._reloadLayerActionTriggered],
                ['show_edit_text', 'Show Edit Text', None, self._showEditTextActionTriggered],
                ['apply_changes', 'Apply Changes', 'Ctrl+Shift+A', self._applyActionTriggered],
                ['live_update', 'Live Update', None, self._liveUpdateActionTriggered],
                ['save_file', 'Save Layer', 'Ctrl+S', self._saveLayerActionTriggered],
                ['export_file', 'Export', 'Ctrl+E', self._exportActionTriggered],
            ]],
            ['Edit', [
                ['create_node', 'Create Node', 'Tab', self._createNodeActionTriggered],
                ['select_all_node', 'Select All', 'Ctrl+A', self._selectAllActionTriggered],
                ['copy_node', 'Copy', 'Ctrl+C', self._copyActionTriggered],
                ['cut_node', 'Cut', 'Ctrl+X', self._cutActionTriggered],
                ['paste_node', 'Paste', 'Ctrl+V', self._pasteActionTriggered],
                ['disable_selection', 'Disable Selection', 'D', self._disableSelectionActionTriggered],
                ['delete_selection', 'Delete Selection', 'Del', self._deleteSelectionActionTriggered],
                ['enter_node', 'Enter', 'Ctrl+Return', self._enterActionTriggered],
                ['force_enter_node', 'Force Enter', 'Ctrl+Shift+Return', self._forceEnterActionTriggered],
            ]],
            ['View', [
                ['layout_nodes', 'Layout Nodes', None, self._layoutActionTriggered],
                ['frame_selection', 'Frame Selection', None, self._frameSelectionActionTriggered],
            ]]
        ]
        actions.extend(self._addedActions)
        return actions

    def _addSubMenus(self, menu, menus):
        for menuL in menus:
            name = menuL[0]

            if isinstance(menuL[1], list):
                findMenus = menu.findChildren(QtWidgets.QMenu, name)
                if len(findMenus) > 0:
                    subMenu = findMenus[0]
                else:
                    subMenu = QtWidgets.QMenu(name, menu)
                    subMenu.setObjectName(name)
                    menu.addMenu(subMenu)

                self._addSubMenus(subMenu, menuL[1])
            else:
                label = menuL[1]
                short_cut = menuL[2]
                func = menuL[3]
                self._addAction(name, label, menu, shortCut=short_cut, triggerFunc=func)

    def _setMenus(self):
        self._addSubMenus(self.menuBar(), self._getMenuActions())

    def _addAction(self, name, label, menu, shortCut=None, triggerFunc=None):
        action = QtWidgets.QAction(label, menu)
        menu.addAction(action)
        if name in self._actionShortCutMap:
            shortCut = self._actionShortCutMap.get(name)
        if shortCut is not None:
            action.setShortcut(shortCut)
        if triggerFunc is not None:
            action.triggered.connect(triggerFunc)

    def _initUI(self):
        self.setWindowTitle('Usd Node Graph')
        self.setDockNestingEnabled(True)
        self.setTabPosition(QtCore.Qt.AllDockWidgetAreas, QtWidgets.QTabWidget.North)

        self._geometry = None
        self._state = None

        self._setMenus()

        self.nodeGraphTab = NodeGraphTab(parent=self)
        self.buttonsWidget = QtWidgets.QWidget(parent=self)
        buttonLayout = QtWidgets.QHBoxLayout()
        buttonLayout.setAlignment(QtCore.Qt.AlignRight)
        buttonLayout.setContentsMargins(0, 0, 10, 0)
        self.buttonsWidget.setLayout(buttonLayout)
        self.nodeGraphTab.setCornerWidget(self.buttonsWidget, QtCore.Qt.TopRightCorner)

        self.applyButton = ApplyButton()
        self.reloadButton = QtWidgets.QPushButton()
        self.reloadButton.setIcon(resource.get_qicon('btn', 'refresh_blue.png'))
        buttonLayout.addWidget(self.applyButton)
        buttonLayout.addWidget(self.reloadButton)

        self.parameterPanel = ParameterPanel(parent=self)
        self.timeSlider = TimeSliderWidget()
        self.editTextEdit = QtWidgets.QTextEdit()

        self._addNewScene()

        self.nodeGraphDock = DockWidget(title='Node Graph', objName='nodeGraphDock')
        self.nodeGraphDock.setWidget(self.nodeGraphTab)
        self.parameterPanelDock = DockWidget(title='Parameters', objName='parameterPanelDock')
        self.parameterPanelDock.setWidget(self.parameterPanel)
        self.timeSliderDock = DockWidget(title='Time Slider', objName='timeSliderDock')
        self.timeSliderDock.setWidget(self.timeSlider)
        self.textEditDock = DockWidget(title='Edit Text', objName='textEditDock')
        self.textEditDock.setWidget(self.editTextEdit)

        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.nodeGraphDock)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.parameterPanelDock)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.timeSliderDock)

        self._docks.append(self.nodeGraphDock)
        self._docks.append(self.parameterPanelDock)
        self._docks.append(self.timeSliderDock)
        self._docks.append(self.textEditDock)

        for widgetClass, name, label in self._addedWidgetClasses:
            dock = DockWidget(title=label, objName=name)
            widget = widgetClass()
            dock.setWidget(widget)

            self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
            self._docks.append(dock)

        self._getUiPref()

    def _dockMaxRequired(self):
        dockWidget = self.sender()
        if dockWidget == self._maxDock:
            # for w in self._docks:
            #     w.setVisible(True)
            self._maxDock = None

            self.restoreState(self._state)
        else:
            self._state = self.saveState()

            for w in self._docks:
                w.setVisible(w == dockWidget)
            self._maxDock = dockWidget

    def _switchScene(self):
        self.currentScene = self.nodeGraphTab.currentWidget()
        if self.currentScene is not None:
            self.currentSceneChanged.emit(self.currentScene.scene)
            self.currentScene.scene.setAsEditTarget()
            stage = self.currentScene.scene.stage
            self.timeSlider.setStage(stage)

    def _addUsdFile(self, usdFile, assetPath=None):
        if assetPath is None:
            assetPath = usdFile
        stage = Usd.Stage.Open(usdFile)
        stage.Reload()
        self._addStage(stage, assetPath=assetPath)

    def _addStage(self, stage, layer=None, assetPath=None):
        if layer is None:
            layer = stage.GetRootLayer()

        self._addScene(stage, layer, assetPath)
        GraphState.executeCallbacks(
            'stageAdded',
            stage=stage, layer=layer
        )

    def _addNewScene(self, stage=None, layer=None, assetPath=None):
        newScene = GraphicsSceneWidget(
            parent=self
        )
        if stage is not None:
            newScene.setStage(stage, layer, assetPath, reset=False)
            GraphState.setTimeIn(stage.GetStartTimeCode(), stage)
            GraphState.setTimeOut(stage.GetEndTimeCode(), stage)
            GraphState.setCurrentTime(stage.GetStartTimeCode(), stage)

        self.scenes.append(newScene)
        self.nodeGraphTab.addTab(newScene, 'Scene')

        newScene.itemDoubleClicked.connect(self._itemDoubleClicked)
        newScene.enterFileRequired.connect(self._enterFileRequired)
        newScene.enterLayerRequired.connect(self._enterLayerRequired)
        newScene.scene.nodeDeleted.connect(self._nodeDeleted)

        self.nodeGraphTab.setCurrentWidget(newScene)
        # self._switchScene()

        return newScene

    def _addScene(self, stage, layer, assetPath):
        newScene = None
        for scene in self.scenes:
            if scene.stage == stage and scene.layer == layer:
                self.nodeGraphTab.setCurrentWidget(scene)
                return

        if newScene is None:
            newScene = self._addNewScene(stage, layer, assetPath)
            newScene.scene.resetScene()

        # newScene.setStage(stage, layer)
        self.nodeGraphTab.setTabText(len(self.scenes) - 1, os.path.basename(layer.realPath))
        self.nodeGraphTab.setTabToolTip(len(self.scenes) - 1, layer.realPath)

        # self._switchScene()

    def _tabCloseRequest(self, index):
        if self.nodeGraphTab.count() > 0:
            scene = self.nodeGraphTab.widget(index)
            self.nodeGraphTab.removeTab(index)
            self.scenes.remove(scene)

    def _tabChanged(self, index):
        self._switchScene()

    def _updateButtonClicked(self):
        self.currentScene.applyChanges()

    def _itemDoubleClicked(self, item):
        self.parameterPanel.addNode(item)
        self.entityItemDoubleClicked.emit(item)

    def _enterFileRequired(self, usdFile, assetPath, force=False):
        usdFile = str(usdFile)
        if not force and not isEditable(usdFile):
            QtWidgets.QMessageBox.warning(None, 'Warning', 'The file:\n{}\ncan\'t be accessed'.format(assetPath))
            return
        self._addUsdFile(usdFile, assetPath)

    def _enterLayerRequired(self, stage, layer, assetPath, force=False):
        if not force and not isEditable(layer.realPath):
            QtWidgets.QMessageBox.warning(None, 'Warning', 'The layer:\n{}\ncan\'t be accessed'.format(assetPath))
            return
        self._addScene(stage, layer, assetPath)

    def _nodeDeleted(self, node):
        self.parameterPanel.removeNode(node.name())

    def _openActionTriggered(self):
        usdFile = QtWidgets.QFileDialog.getOpenFileName(None, 'Select File', filter='USD(*.usda *.usd *.usdc)')
        if isinstance(usdFile, tuple):
            usdFile = usdFile[0]
        usdFile = str(usdFile)
        if os.path.exists(usdFile):
            self.setUsdFile(usdFile)

    def _reopenActionTriggered(self):
        if self._usdFile is not None:
            self.setUsdFile(self._usdFile)

    def _reloadStageActionTriggered(self):
        currentStage = self.currentScene.stage
        for scene in self.scenes:
            if scene.stage == currentStage:
                index = self.nodeGraphTab.indexOf(scene)
                self.nodeGraphTab.removeTab(index)
                self.scenes.remove(scene)
        self.addStage(currentStage)

    def _reloadLayerActionTriggered(self):
        self.currentScene.scene.reloadLayer()

    def _showEditTextActionTriggered(self):
        self.textEditDock.setVisible(True)
        self.textEditDock.resize(500, 500)
        self.editTextEdit.setText(self.currentScene.exportToString())

    def _exportActionTriggered(self):
        self.currentScene.exportToFile()

    def _saveLayerActionTriggered(self):
        self.currentScene.saveFile()

    def _applyActionTriggered(self):
        self.currentScene.applyChanges()

    def _liveUpdateActionTriggered(self):
        GraphState.setLiveUpdate(1 - GraphState.isLiveUpdate())

    def _createNodeActionTriggered(self):
        self.currentScene.view.showFloatEdit()

    def _selectAllActionTriggered(self):
        self.currentScene.scene.selectAll()

    def _copyActionTriggered(self):
        nodesString = self.currentScene.scene.getSelectedNodesAsXml()
        cb = QtWidgets.QApplication.clipboard()
        cb.setText(nodesString)

    def _pasteActionTriggered(self):
        nodesString = str(QtWidgets.QApplication.clipboard().text())
        nodes = self.currentScene.scene.pasteNodesFromXml(nodesString)

    def _cutActionTriggered(self):
        self._copyActionTriggered()
        self._deleteSelectionActionTriggered()

    def _enterActionTriggered(self):
        self.currentScene.scene.enterSelection()

    def _forceEnterActionTriggered(self):
        self.currentScene.scene.forceEnterSelection()

    def _frameSelectionActionTriggered(self):
        self.currentScene.scene.frameSelection()

    def _layoutActionTriggered(self):
        self.currentScene.scene.layoutNodes()

    def _disableSelectionActionTriggered(self):
        self.currentScene.scene.disableSelection()

    def _deleteSelectionActionTriggered(self):
        self.currentScene.scene.deleteSelection()

    def _clearScenes(self):
        for i in range(self.nodeGraphTab.count()):
            self._tabCloseRequest(i)

    def setUsdFile(self, usdFile):
        self._usdFile = usdFile
        self._clearScenes()
        self._addUsdFile(usdFile)

    def addUsdFile(self, usdFile):
        self._addUsdFile(usdFile)

    def setStage(self, stage, layer=None):
        self._clearScenes()
        self._addStage(stage, layer)

    def addStage(self, stage, layer=None):
        self._addStage(stage, layer)

    def findNodeAtPath(self, path):
        nodes = self.currentScene.scene.findNodeAtPath(path)
        return nodes

    def createNode(self, nodeType):
        node = self.currentScene.scene.createNode(nodeType)
        return node

    def closeEvent(self, event):
        super(UsdNodeGraph, self).closeEvent(event)
        write_setting(User_Setting, 'nodegraph_geo/{}'.format(self.app), value=self.saveGeometry())
        write_setting(User_Setting, 'nodegraph_state/{}'.format(self.app), value=self.saveState())
        self.mainWindowClosed.emit()

    def _getUiPref(self):
        geo = read_setting(
            User_Setting,
            'nodegraph_geo/{}'.format(self.app),
            to_type='bytearray')
        state = read_setting(
            User_Setting,
            'nodegraph_state/{}'.format(self.app),
            to_type='bytearray')

        self.restoreGeometry(geo)
        self.restoreState(state)


