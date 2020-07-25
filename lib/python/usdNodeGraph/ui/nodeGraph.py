# -*- coding: utf-8 -*-
# __author__ = 'XingHuan'
# 8/29/2018

import os
import sys
from pxr import Usd
from usdNodeGraph.module.sqt import *
from usdNodeGraph.ui.graph.view import GraphicsSceneWidget
from usdNodeGraph.ui.graph.node import NodeItem
from usdNodeGraph.ui.graph.const import Const
from usdNodeGraph.ui.parameter.param_panel import ParameterPanel
from usdNodeGraph.ui.utils.state import GraphState
from usdNodeGraph.ui.timeSlider import TimeSliderWidget
from usdNodeGraph.utils.settings import User_Setting, read_setting, write_setting


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
    _actionShortCutMap = {}

    @classmethod
    def registerActionShortCut(cls, actionName, shortCut):
        cls._actionShortCutMap.update({
            actionName: shortCut
        })

    def __init__(
            self,
            parent=None
    ):
        super(UsdNodeGraph, self).__init__(parent=parent)

        self.currentScene = None
        self.scenes = []
        self._docks = []
        self._maxDock = None

        self._initUI()
        self._createSignal()

    def _createSignal(self):
        self.nodeGraphTab.tabCloseRequested.connect(self._tabCloseRequest)
        self.nodeGraphTab.currentChanged.connect(self._tabChanged)

        for dock in self._docks:
            dock.maximizedRequired.connect(self._dockMaxRequired)

    def _setMenus(self):
        self.fileMenu = QtWidgets.QMenu('File', self)
        self.menuBar().addMenu(self.fileMenu)
        self._addAction('open_file', 'Open', self.fileMenu, shortCut='Ctrl+O', triggerFunc=self._openActionTriggered)
        self._addAction('reload_stage', 'Reload Stage', self.fileMenu, shortCut='Alt+Shift+R', triggerFunc=self._reloadStageActionTriggered)
        self._addAction('reload_layer', 'Reload Layer', self.fileMenu, shortCut='Alt+R', triggerFunc=self._reloadLayerActionTriggered)

        self._addAction('show_edit_text', 'Show Edit Text', self.fileMenu, shortCut=None, triggerFunc=self._showEditTextActionTriggered)
        self._addAction('apply_changes', 'Apply', self.fileMenu, shortCut='Ctrl+Shift+A', triggerFunc=self._applyActionTriggered)
        self._addAction('export_file', 'Export', self.fileMenu, shortCut='Ctrl+E', triggerFunc=self._exportActionTriggered)

        self.editMenu = QtWidgets.QMenu('Edit', self)
        self.menuBar().addMenu(self.editMenu)
        self._addAction('create_node', 'Create New', self.editMenu, shortCut='Tab', triggerFunc=self._createNodeActionTriggered)
        self._addAction('select_all_node', 'Select All', self.editMenu, shortCut='Ctrl+A', triggerFunc=self._selectAllActionTriggered)
        self._addAction('copy_node', 'Copy', self.editMenu, shortCut='Ctrl+C', triggerFunc=self._copyActionTriggered)
        self._addAction('cut_node', 'Cut', self.editMenu, shortCut='Ctrl+X', triggerFunc=self._cutActionTriggered)
        self._addAction('paste_node', 'Paste', self.editMenu, shortCut='Ctrl+V', triggerFunc=self._pasteActionTriggered)
        self._addAction('frame_selection', 'Frame Selection', self.editMenu, triggerFunc=self._frameSelectionActionTriggered)
        self._addAction('disable_selection', 'Disable Selection', self.editMenu, shortCut='D', triggerFunc=self._disableSelectionActionTriggered)
        self._addAction('delete_selection', 'Delete Selection', self.editMenu, shortCut='Del', triggerFunc=self._deleteSelectionActionTriggered)
        self._addAction('enter_node', 'Enter', self.editMenu, shortCut='Ctrl+Return', triggerFunc=self._enterActionTriggered)

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

        self._geometry = None
        self._state = None

        self._setMenus()

        self.nodeGraphTab = NodeGraphTab(parent=self)
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

    def _addUsdFile(self, usdFile):
        stage = Usd.Stage.Open(usdFile)
        self._addStage(stage)

    def _addStage(self, stage, layer=None):
        if layer is None:
            layer = stage.GetRootLayer()
        self._addScene(stage, layer)

    def _addNewScene(self, stage=None, layer=None):
        newScene = GraphicsSceneWidget(
            parent=self
        )
        if stage is not None:
            newScene.setStage(stage, layer, reset=False)
            GraphState.setTimeIn(stage.GetStartTimeCode(), stage)
            GraphState.setTimeOut(stage.GetEndTimeCode(), stage)
            GraphState.setCurrentTime(stage.GetStartTimeCode(), stage)

        self.scenes.append(newScene)
        self.nodeGraphTab.addTab(newScene, 'Scene')

        newScene.itemDoubleClicked.connect(self._itemDoubleClicked)
        newScene.enterFileRequired.connect(self._enterFileRequired)
        newScene.enterLayerRequired.connect(self._enterLayerRequired)

        self.nodeGraphTab.setCurrentWidget(newScene)
        # self._switchScene()

        return newScene

    def _addScene(self, stage, layer):
        newScene = None
        for scene in self.scenes:
            if scene.stage == stage and scene.layer == layer:
                self.nodeGraphTab.setCurrentWidget(scene)
                return

        if newScene is None:
            newScene = self._addNewScene(stage, layer)
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

    def _itemDoubleClicked(self, item):
        self.parameterPanel.addNode(item)
        self.entityItemDoubleClicked.emit(item)

    def _enterFileRequired(self, usdFile):
        usdFile = str(usdFile)
        self._addUsdFile(usdFile)

    def _enterLayerRequired(self, stage, layer):
        self._addScene(stage, layer)

    def _openActionTriggered(self):
        usdFile = QFileDialog.getOpenFileName(None, 'Select File', filter='USD(*.usda *.usd *.usdc)')
        if isinstance(usdFile, tuple):
            usdFile = usdFile[0]
        if os.path.exists(usdFile):
            self.setUsdFile(usdFile)

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
        self.editTextEdit.setText(self.currentScene.exportToString())

    def _exportActionTriggered(self):
        self.currentScene.exportToFile()

    def _applyActionTriggered(self):
        self.currentScene.applyChanges()

    def _createNodeActionTriggered(self):
        self.currentScene.view.showFloatEdit()

    def _selectAllActionTriggered(self):
        self.currentScene.scene.selectAll()

    def _copyActionTriggered(self):
        nodesString = self.currentScene.scene.getSelectedNodesAsString()
        cb = QtWidgets.QApplication.clipboard()
        cb.setText(nodesString)

    def _pasteActionTriggered(self):
        nodesString = QtWidgets.QApplication.clipboard().text()
        nodes = self.currentScene.scene.pasteNodesFromString(nodesString)

    def _cutActionTriggered(self):
        self._copyActionTriggered()
        self._deleteSelectionActionTriggered()

    def _enterActionTriggered(self):
        self.currentScene.scene.enterSelection()

    def _frameSelectionActionTriggered(self):
        self.currentScene.scene.frameSelection()

    def _disableSelectionActionTriggered(self):
        self.currentScene.scene.disableSelection()

    def _deleteSelectionActionTriggered(self):
        self.currentScene.scene.deleteSelection()

    def _clearScenes(self):
        for i in range(self.nodeGraphTab.count()):
            self._tabCloseRequest(i)

    def setUsdFile(self, usdFile):
        self._clearScenes()
        self._addUsdFile(usdFile)

    def addUsdFile(self, usdFile):
        self._addUsdFile(usdFile)

    def setStage(self, stage, layer=None):
        self._clearScenes()
        self._addStage(stage, layer)

    def addStage(self, stage, layer=None):
        self._addStage(stage, layer)

    def closeEvent(self, event):
        super(UsdNodeGraph, self).closeEvent(event)
        write_setting(User_Setting, 'nodegraph_geo', value=self.saveGeometry())
        write_setting(User_Setting, 'nodegraph_state', value=self.saveState())

    def _getUiPref(self):
        geo = read_setting(
            User_Setting,
            'nodegraph_geo',
            to_type='bytearray')
        state = read_setting(
            User_Setting,
            'nodegraph_state',
            to_type='bytearray')

        self.restoreGeometry(geo)
        self.restoreState(state)


