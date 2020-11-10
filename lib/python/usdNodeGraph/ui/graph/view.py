# -*- coding: utf-8 -*-

import os
import re
import json
import time
from pxr import Usd, Sdf, Ar
from usdNodeGraph.module.sqt import *
from usdNodeGraph.utils.const import VIEWPORT_FULL_UPDATE
from usdNodeGraph.core.node import (
    Node, TransformNode, AttributeSetNode, MetadataNode,
    RelationshipSetNode, MaterialAssignNode, LIST_EDITOR_PROXY_OPS
)
from .nodeItem import NodeItem
from .other.pipe import Pipe
from .other.port import Port
from usdNodeGraph.utils.log import get_logger, log_cost_time
from usdNodeGraph.core.state import GraphState
from usdNodeGraph.core.parse._xml import ET, convertToString
from usdNodeGraph.utils.res import resource
from usdNodeGraph.ui.utils.menu import WithMenuObject
from usdNodeGraph.ui.utils.drop import DropWidget


logger = get_logger('usdNodeGraph.view')


NODE_NAME_PATTERN = re.compile('(?P<suffix>[^\d]*)(?P<index>\d+)')
VARIANT_PRIM_PATH_PATTERN = re.compile('.*{(?P<variantSet>.+)=(?P<variant>.+)}$')

VIEW_FILL_COLOR = QtGui.QColor(38, 38, 38)
VIEW_LINE_COLOR = QtGui.QColor(55, 55, 55)
DISABLE_LINE_COLOR = QtGui.QColor(95, 75, 75)
VIEW_CENTER_LINE_COLOR = QtGui.QColor(80, 80, 60, 50)
VIEW_GRID_WIDTH = 200
VIEW_GRID_HEIGHT = 100

VIEW_ZOOM_STEP = 1.1


def isEditable(realPath):
    if GraphState.hasFunction('isFileEditable') and realPath is not None:
        editAble = GraphState.executeFunction('isFileEditable', realPath)
        return editAble
    return True


class FloatLineEdit(QtWidgets.QFrame):
    editFinished = QtCore.Signal(str)

    def __init__(self, *args, **kwargs):
        super(FloatLineEdit, self).__init__(*args, **kwargs)

        self.masterLayout = QtWidgets.QHBoxLayout()
        self.setLayout(self.masterLayout)

        self._edit = QtWidgets.QLineEdit()
        self.masterLayout.addWidget(self._edit)

        self.setFixedWidth(200)
        self.setStyleSheet('QFrame{border-radius: 5px}')

        self._edit.editingFinished.connect(self._editFinished)
        self._edit.returnPressed.connect(self._returnPressed)

    def _editFinished(self):
        # self.editFinished.emit(self._edit.text())
        self.setVisible(False)

    def _returnPressed(self):
        self.editFinished.emit(self._edit.text())
        self.setVisible(False)
        self.parent().setFocus()
        self._edit.setFocus()

    def reset(self):
        allNodeClass = Node.getAllNodeClassNames()
        completer = QtWidgets.QCompleter(allNodeClass)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self._edit.setCompleter(completer)
        self._edit.setText('')

    def setVisible(self, bool):
        super(FloatLineEdit, self).setVisible(bool)
        if bool:
            self._edit.setFocus()


class FormatSwitchButton(QtWidgets.QPushButton):
    def __init__(self):
        super(FormatSwitchButton, self).__init__()
        
        self._format = 'usd'
        self._tempNodes = ''

        self.setFixedSize(30, 30)
        self.setIconSize(QtCore.QSize(25, 25))
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setStyleSheet("""
        QPushButton{
            background: transparent;
            border: none;
        }
        """)

        self.updateIcon()

        self.clicked.connect(self.switch)

    def setFormat(self, format='usd'):
        self._format = format
        self.updateIcon()

    def getFormat(self):
        return self._format

    def switch(self):
        if self._format == 'usd':
            self._format = 'ung'
        elif self._format == 'ung':
            self._format = 'usd'
        self.updateIcon()

    def updateIcon(self):
        if self._format == 'usd':
            icon = resource.get_qicon('icon', 'UsdLogo.png')
        elif self._format == 'ung':
            icon = resource.get_qicon('icon', 'UngLogo.png')
        self.setIcon(icon)
    
    def writeTempNodes(self, xmlString):
        self._tempNodes = xmlString
    
    def getTempNodes(self):
        return self._tempNodes


class FloatWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(FloatWidget, self).__init__(*args, **kwargs)

        self.masterLayout = QtWidgets.QHBoxLayout()
        self.setLayout(self.masterLayout)

        self.switchButton = FormatSwitchButton()
        self.masterLayout.addWidget(self.switchButton)


class GraphicsView(QtWidgets.QGraphicsView, DropWidget, WithMenuObject):
    def __init__(self, *args, **kwargs):
        super(GraphicsView, self).__init__(*args, **kwargs)
        DropWidget.__init__(self)

        self.setAcceptExts(['.abc', '.usd', '.usda', '.usdc'])
        # self.addDropLabel()

        self.currentZoom = 1.0
        self.panningMult = 2.0 * self.currentZoom
        self.panning = False
        self.keyZooming = False
        self.clickedPos = QtCore.QPoint(0, 0)

        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        if VIEWPORT_FULL_UPDATE == '0':
            self.setViewportUpdateMode(QtWidgets.QGraphicsView.SmartViewportUpdate)
        else:
            self.setViewportUpdateMode(QtWidgets.QGraphicsView.FullViewportUpdate)
        # self.setRenderHint(QtGui.QPainter.Antialiasing)

        self._createNewFloatEdit = FloatLineEdit(self)
        self._createNewFloatEdit.setVisible(False)

        self._floatWidget = FloatWidget(self)

        self._createNewFloatEdit.editFinished.connect(self._floatEditFinished)
        self._floatWidget.switchButton.clicked.connect(self._formatSwitchClicked)

    def dragEnterEvent(self, QDragEnterEvent):
        DropWidget.dragEnterEvent(self, QDragEnterEvent)

    def dragLeaveEvent(self, QDragLeaveEvent):
        DropWidget.dragLeaveEvent(self, QDragLeaveEvent)

    def dragMoveEvent(self, QDragMoveEvent):
        DropWidget.dragMoveEvent(self, QDragMoveEvent)

    def dropEvent(self, QDropEvent):
        DropWidget.dropEvent(self, QDropEvent)

    def afterFilesDrop(self, acceptFiles):
        pos = None
        for i in acceptFiles:
            refNode = self.scene().createNode('Reference', pos=pos)
            refNode.parameter('assetPath').setValue(i)
            x = refNode.parameter('x').getValue()
            y = refNode.parameter('y').getValue()
            pos = [x + 200, y]

    def _zoom(self, zoom):
        self.scale(zoom, zoom)
        self.currentZoom = self.transform().m11()
        self._resizeScene()

    def getCenterPos(self):
        center = self.mapToScene(QtCore.QPoint(
            self.viewport().width() / 2,
            self.viewport().height() / 2
        ))
        return center

    def _resizeScene(self, setLabel=True):
        center = self.getCenterPos()
        w = self.viewport().width() / self.currentZoom * 2 + 25000
        h = self.viewport().height() / self.currentZoom * 2 + 25000

        self.scene().setSceneRect(QtCore.QRectF(
            center.x() - w / 2,
            center.y() - h / 2,
            w,
            h
        ))

        self._setAntialiasing()

        if setLabel:
            self._setLabelVisible()

    def _setAntialiasing(self):
        antialiasing = True if self.currentZoom >= 0.1 else False
        self.setRenderHint(QtGui.QPainter.Antialiasing, antialiasing)

    def _setLabelVisible(self):
        showPortLabel = True if self.currentZoom >= 1 else False
        showNodeLabel = True if self.currentZoom >= 0.5 else False

        point1 = self.mapToScene(QtCore.QPoint(-20, -20))
        point2 = self.mapToScene(QtCore.QPoint(self.viewport().width(), self.viewport().height()))
        rect = QtCore.QRectF(point1, point2)

        for node in self.scene().allNodes():
            node.setLabelVisible(showNodeLabel and rect.contains(node.pos()))
            for port in node.ports:
                port.setLabelVisible(showPortLabel and rect.contains(port.scenePos()))

    def focusNextPrevChild(self, bool):
        return False

    def keyReleaseEvent(self, event):
        super(GraphicsView, self).keyReleaseEvent(event)
        if not self._createNewFloatEdit.isVisible():
            if event.key() == QtCore.Qt.Key_F:
                self.scene().frameSelection()

    def fitTo(self, items=[]):
        if len(items) == 0:
            for item in self.scene().items():
                if isinstance(item, NodeItem):
                    items.append(item)

        max_x = items[0].pos().x()
        min_x = items[0].pos().x()
        max_y = items[0].pos().y()
        min_y = items[0].pos().y()
        for item in items:
            max_x = max(item.pos().x(), max_x)
            min_x = min(item.pos().x(), min_x)
            max_y = max(item.pos().y(), max_y)
            min_y = min(item.pos().y(), min_y)
        center_x = (max_x + min_x) / 2 + 100
        center_y = (max_y + min_y) / 2 + 40
        width = max_x - min_x
        height = max_y - min_y

        zoom_x = 1 / max(1, float(width + 1000) / self.viewport().width()) / self.currentZoom
        zoom_y = 1 / max(1, float(height + 1000) / self.viewport().height()) / self.currentZoom
        zoom = min(zoom_x, zoom_y)
        self.scale(zoom, zoom)
        self.currentZoom = self.transform().m11()
        self._resizeScene()

        self.centerOn(QtCore.QPointF(center_x, center_y))

    def mousePressEvent(self, event):
        """Initiate custom panning using middle mouse button."""
        selectedItems = self.scene().selectedItems()
        self.clickedPos = event.pos()

        if self.panning:
            if event.button() == QtCore.Qt.RightButton:
                self.keyZooming = True
                self.panning = False
                self.setCursor(QtCore.Qt.ArrowCursor)
                return

        if event.button() == QtCore.Qt.MiddleButton:
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
            self.panning = True
            self.prevPos = event.pos()
            self.prevCenter = self.getCenterPos()
            self.setCursor(QtCore.Qt.SizeAllCursor)
        elif event.button() == QtCore.Qt.LeftButton:
            self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
        super(GraphicsView, self).mousePressEvent(event)
        if event.button() == QtCore.Qt.MiddleButton:
            for item in selectedItems:
                item.setSelected(True)
        self._highlightConnection()

    def mouseMoveEvent(self, event):
        if self.keyZooming:
            mouseMove = event.pos() - self.prevPos
            mouseMoveY = mouseMove.y()
            if mouseMoveY > 0: #  zoom in
                zoom = mouseMoveY * 0.01 + 1
                self._zoom(zoom)
            elif mouseMoveY < 0:
                zoom = 1.0 / (-mouseMoveY * 0.01 + 1)
                self._zoom(zoom)

            self.prevPos = event.pos()
        if self.panning:
            mouseMove = event.pos() - self.prevPos
            newCenter = QtCore.QPointF(
                self.prevCenter.x() - mouseMove.x() / self.currentZoom,
                self.prevCenter.y() - mouseMove.y() / self.currentZoom
            )
            self.centerOn(newCenter)
            self._resizeScene(setLabel=False)
            return
        super(GraphicsView, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.panning:
            self.panning = False
            self.setCursor(QtCore.Qt.ArrowCursor)
        if self.keyZooming:
            self.keyZooming = False

        super(GraphicsView, self).mouseReleaseEvent(event)

        self._highlightConnection()
        self.clickedPos = event.pos()
        self._resizeScene()

    def wheelEvent(self, event):
        positive = event.delta() >= 0
        zoom = VIEW_ZOOM_STEP if positive else 1.0 / VIEW_ZOOM_STEP
        self._zoom(zoom)

    def drawForeground(self, painter, rect):
        editAble = self.scene().editable
        if not editAble:
            self.drawDisableLines(painter, rect)

    def drawDisableLines(self, painter, rect):
        pen = QtGui.QPen(DISABLE_LINE_COLOR)
        pen.setCosmetic(True)
        pen.setWidth(1)
        painter.setPen(pen)

        lines = []
        lw = 50

        w = self.viewport().width()
        h = self.viewport().height()

        for i in range(int(w / lw)):
            point1 = self.mapToScene(QtCore.QPoint(i * lw, 0))
            point2 = self.mapToScene(QtCore.QPoint(0, i * lw))

            lines.append(QtCore.QLineF(point1, point2))

        for i in range(int(h / lw)):
            point1 = self.mapToScene(QtCore.QPoint(w, i * lw))
            point2 = self.mapToScene(QtCore.QPoint(w - (h - i * lw), h))

            lines.append(QtCore.QLineF(point1, point2))

        painter.drawLines(lines)

    def drawBackground(self, painter, rect):
        pen = QtGui.QPen(VIEW_LINE_COLOR)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(QtGui.QBrush(VIEW_FILL_COLOR))

        painter.drawRect(rect)
        lines = []
        scale = max(int(1 / self.currentZoom / 2), 1)
        line_w = VIEW_GRID_WIDTH * scale
        line_h = VIEW_GRID_HEIGHT * scale

        point1 = self.mapToScene(QtCore.QPoint(0, 0))
        point2 = self.mapToScene(QtCore.QPoint(self.viewport().width(), self.viewport().height()))

        for i in range(int(point1.y() / line_h), int(point2.y() / line_h) + 1):
            lines.append(QtCore.QLineF(
                QtCore.QPoint(rect.x(), i * line_h),
                QtCore.QPoint(rect.x() + rect.width(), i * line_h)
            ))

        for i in range(int(point1.x() / line_w), int(point2.x() / line_w) + 1):
            lines.append(QtCore.QLineF(
                QtCore.QPoint(i * line_w, rect.y()),
                QtCore.QPoint(i * line_w, rect.y() + rect.height())
            ))
        painter.drawLines(lines)

        painter.setPen(QtGui.QPen(VIEW_CENTER_LINE_COLOR))
        painter.drawLine(QtCore.QLineF(QtCore.QPoint(rect.x(), 0), QtCore.QPoint(rect.x() + rect.width(), 0)))
        painter.drawLine(QtCore.QLineF(QtCore.QPoint(0, rect.y()), QtCore.QPoint(0, rect.y() + rect.height())))

    def _highlightConnection(self):
        for item in self.scene().items():
            if isinstance(item, Port):
                for pipe in item.pipes:
                    pipe.setLineColor(highlight=False)
            # if isinstance(item, NodeItem):
            #     item.setHighlight(False)
        for item in self.scene().selectedItems():
            if isinstance(item, NodeItem):
                for port in item.ports:
                    for pipe in port.pipes:
                        pipe.setLineColor(highlight=True)

    def showFloatEdit(self):
        self._createNewFloatEdit.move(self.clickedPos)
        self._createNewFloatEdit.reset()
        self._createNewFloatEdit.setVisible(True)

    def _floatEditFinished(self, text):
        text = str(text)
        scenePos = self.mapToScene(self.clickedPos)
        node = self.scene().createNode(text, pos=[scenePos.x(), scenePos.y()])

    def _formatSwitchClicked(self):
        format = self._floatWidget.switchButton.getFormat()
        if format == 'usd':
            xmlString = self.scene().getAllNodesAsXml()
            self._floatWidget.switchButton.writeTempNodes(xmlString)
            self.scene().resetScene(forceFromLayer=True)
        else:
            xmlString = self._floatWidget.switchButton.getTempNodes()
            self.scene().resetScene(forceFromLayer=False, xmlString=xmlString)

    def _getContextMenus(self):
        actions = []
        groupDict = Node.getNodesByGroup()
        groups = groupDict.keys()
        groups.sort()
        for group in groups:
            nodeActions = []
            nodes = groupDict[group]
            for node in nodes:
                nodeActions.append([node.nodeType, node.nodeType, None, self._nodeActionTriggered])
            actions.append([group, nodeActions])

        return actions

    def _createContextMenu(self):
        self.menu = QtWidgets.QMenu(self)
        menus = []
        scenePos = self.mapToScene(self.clickedPos)
        item = self.scene().itemAt(scenePos, QtGui.QTransform())
        if item is None:
            menus = self._getContextMenus()
        elif isinstance(item, NodeItem):
            menus = item.getContextMenus()
        elif isinstance(item.parentItem(), NodeItem):
            menus = item.parentItem().getContextMenus()
        self._addSubMenus(self.menu, menus)

    def contextMenuEvent(self, event):
        super(GraphicsView, self).contextMenuEvent(event)
        self._createContextMenu()
        self.menu.move(QtGui.QCursor().pos())
        self.menu.show()

    def _nodeActionTriggered(self):
        nodeType = self.sender().objectName()
        scenePos = self.mapToScene(self.clickedPos)
        self.scene().createNode(nodeType, pos=[scenePos.x(), scenePos.y()])


class GraphicsSceneWidget(QtWidgets.QWidget):
    itemDoubleClicked = QtCore.Signal(object)
    showWidgetSignal = QtCore.Signal(int)
    enterFileRequired = QtCore.Signal(str, str, bool)
    enterLayerRequired = QtCore.Signal(object, object, str, bool)

    def __init__(self, parent=None):
        super(GraphicsSceneWidget, self).__init__(parent=parent)

        self.stage = None
        self.layer = None
        self.assetPath = None

        self._initUI()

        # self.showWidgetSignal.connect(self.show_entity_widget, QtCore.Qt.QueuedConnection)
        self.scene.enterFileRequired.connect(self._enterFileRequired)
        self.scene.enterLayerRequired.connect(self._enterLayerRequired)

    def _initUI(self):

        self.view = GraphicsView()
        self.scene = GraphicsScene(view=self.view, parent=self)
        self.view.setScene(self.scene)
        self.setGeometry(100, 100, 800, 600)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)

        self.scene.setSceneRect(QtCore.QRectF(
            -(self.view.viewport().width() / self.view.currentZoom * 2 + 25000) / 2,
            -(self.view.viewport().height() / self.view.currentZoom * 2 + 25000) / 2,
            self.view.viewport().width() / self.view.currentZoom * 2 + 25000,
            self.view.viewport().height() / self.view.currentZoom * 2 + 25000
        ))

    def _getAbsPath(self, path):
        path = str(path)
        resolver = Ar.GetResolver()
        absLayerPath = resolver.AnchorRelativePath(self.layer.realPath, path)
        return absLayerPath

    def _enterFileRequired(self, usdFile, force=False):
        # for Reference and Payload
        absLayerPath = self._getAbsPath(usdFile)
        self.enterFileRequired.emit(absLayerPath, usdFile, force)

    def _enterLayerRequired(self, layerPath, force=False):
        # for sublayer
        absLayerPath = self._getAbsPath(layerPath)
        layer = Sdf.Layer.FindOrOpen(absLayerPath)
        self.enterLayerRequired.emit(self.stage, layer, layerPath, force)

    def setStage(self, stage, layer=None, assetPath=None, reset=True):
        self.stage = stage
        if layer is None:
            layer = stage.GetRootLayer()
        self.layer = layer
        self.assetPath = assetPath
        self.scene.setStage(self.stage, self.layer, assetPath, reset=reset)

    def exportToString(self):
        return self.scene.exportToString()

    def exportToFile(self):
        self.scene.exportToFile()

    def saveLayer(self):
        self.scene.saveLayer()

    def saveNodes(self):
        self.scene.saveNodes()

    def applyChanges(self):
        self.scene.applyChanges()


class GraphicsScene(QtWidgets.QGraphicsScene):
    enterFileRequired = QtCore.Signal(str, bool)
    enterLayerRequired = QtCore.Signal(str, bool)
    nodeParameterChanged = QtCore.Signal(object)
    nodeDeleted = QtCore.Signal(object)

    def __init__(self, view=None, **kwargs):
        super(GraphicsScene, self).__init__(**kwargs)

        self.view = view

        self.stage = None
        self.layer = None
        self.assetPath = None
        self.editable = True

        self._allNodes = {}
        self._nodesSuffix = {}
        self._primNodes = {}

        self.setSceneRect(QtCore.QRectF(-25000 / 2, -25000 / 2, 25000, 25000))

    def _addLayerNodes(self, rootLayer):
        for index, layerPath in enumerate(rootLayer.subLayerPaths):
            layerOffset = rootLayer.subLayerOffsets[index]
            layerNode = self.createNode('Layer', layerPath=layerPath, layerOffset=layerOffset)
            layerNode.setX(-250)
            layerNode.setY(index * 150)

    def _addChildNode(self, node, upNode, index=0):
        if upNode is not None:
            node.setX(upNode.pos().x() + index * (upNode.w + 50))
            node.setY(upNode.pos().y() + upNode.h + 100)
            node.connectToNode(upNode)

    def _getPrim(self, primSpec, upNode=None):
        skipAttribute = False

        primPath = primSpec.path.pathString
        match = re.match(VARIANT_PRIM_PATH_PATTERN, primPath)
        if match:
            variantSwitchNode = self.createNode(
                'VariantSwitch', primPath=primPath,
                variantSetName=match.group('variantSet'),
                variantSelected=match.group('variant')
            )
            self._addChildNode(variantSwitchNode, upNode)
            upNode = variantSwitchNode
        else:
            # prim define
            specifier = primSpec.specifier
            if specifier == Sdf.SpecifierDef:
                typeName = primSpec.typeName
                if typeName in ['Material', 'Shader']:
                    primNode = self.createNode(
                        typeName, name=primSpec.name, primPath=primPath,
                        primSpec=primSpec
                    )
                    skipAttribute = True
                elif typeName in Node.getAllNodeClassNames():
                    primNode = self.createNode(typeName, primPath=primPath, primSpec=primSpec)
                else:
                    primNode = self.createNode('PrimDefine', primPath=primPath, primSpec=primSpec)
            elif specifier == Sdf.SpecifierOver:
                primNode = self.createNode('PrimOverride', primPath=primPath, primSpec=primSpec)
            else:
                return upNode

            self._addChildNode(primNode, upNode)
            self._addNodeToPrimPath(primNode, primPath)
            upNode = primNode

        # metadata
        _tmpMetadataNodes = {}
        _keys = [key for key in primSpec.ListInfoKeys() if key in MetadataNode.getIgnorePrimInfoKeys()]
        for key in _keys:
            nodeClass = MetadataNode.getMetadataNodeClass(key)
            metadataNode = _tmpMetadataNodes.get(nodeClass.nodeType)
            if metadataNode is None:
                metadataNode = self.createNode(nodeClass.nodeType)
                self._addChildNode(metadataNode, upNode)
                _tmpMetadataNodes.update({nodeClass.nodeType: metadataNode})
            metadataNode.parameter(key).setValueQuietly(primSpec.GetInfo(key))
            upNode = metadataNode

        # reference
        referenceList = primSpec.referenceList
        for op in LIST_EDITOR_PROXY_OPS:
            items = getattr(referenceList, '{}Items'.format(op))
            for reference in items:
                referenceNode = self.createNode('Reference', primPath=primPath, reference=reference, op=op)
                self._addChildNode(referenceNode, upNode)

                upNode = referenceNode

        # payload
        payloadList = primSpec.payloadList
        for op in LIST_EDITOR_PROXY_OPS:
            items = getattr(payloadList, '{}Items'.format(op))
            for payload in items:
                payloadNode = self.createNode('Payload', primPath=primPath, reference=payload, op=op)
                self._addChildNode(payloadNode, upNode)

                upNode = payloadNode

        # attribute
        if not skipAttribute:
            upNode = self._getPrimAttributes(primSpec, upNode)

        # relationship
        upNode = self._getPrimRelationships(primSpec, upNode)

        # variant
        selectedVariantDict = {}
        variantSetNameList = primSpec.variantSetNameList
        variantSetNameItems = variantSetNameList.GetAddedOrExplicitItems()
        variantSelections = primSpec.variantSelections
        if len(variantSetNameItems) > 0:
            variantSets = primSpec.variantSets
            for variantSetName, variantSetSpec in variantSets.items():
                variantSetNode = self.createNode(
                    'VariantSet',
                    primPath=primPath,
                    variantSetName=variantSetSpec.name,
                    options=[v.name for v in variantSetSpec.variantList]
                )
                self._addChildNode(variantSetNode, upNode)

                variantSelected = variantSelections.get(variantSetName)
                variantSelectNode = self.createNode(
                    'VariantSelect', primPath=primPath,
                    variantSetName=variantSetName,
                    variantSelected=variantSelected,
                    options=[v.name for v in variantSetSpec.variantList]
                )
                self._addChildNode(variantSelectNode, variantSetNode)
                selectedVariantDict.update({variantSetName: variantSelected})

                variantList = variantSetSpec.variantList
                for i, variantSpec in enumerate(variantList):
                    variantPrim = variantSpec.primSpec
                    self._getIntoPrim(variantPrim, upNode=variantSelectNode)

        for variantSetName, variantSelected in variantSelections.items():
            if not variantSetName in selectedVariantDict:

                variantNameList = None
                # try to get variant list
                stagePrim = self.stage.GetPrimAtPath(primPath)
                if stagePrim.IsValid():
                    variantSet = stagePrim.GetVariantSet(variantSetName)
                    variantNameList = variantSet.GetVariantNames()

                variantSelectNode = self.createNode(
                    'VariantSelect', primPath=primPath,
                    variantSetName=variantSetName,
                    variantSelected=variantSelected,
                    options=variantNameList
                )
                self._addChildNode(variantSelectNode, upNode)
                upNode = variantSelectNode

        return upNode

    def _getIntoPrim(self, primSpec, upNode):
        primPath = primSpec.path.pathString
        node = upNode
        if primPath != '/':
            node = self._getPrim(primSpec, upNode)
        for childName, child in primSpec.nameChildren.items():
            self._getIntoPrim(child, node)

    def _getPrimAttributes(self, primSpec, upNode):
        attrs = primSpec.attributes.keys()
        if len(attrs) == 0:
            return upNode

        addTransform = TransformNode._checkIsNodeNeeded(attrs)
        if addTransform:
            transformNode = self.createNode('Transform', primPath=primSpec.path.pathString, primSpec=primSpec)
            self._addChildNode(transformNode, upNode)
            upNode = transformNode

        addAttributeSet = AttributeSetNode._checkIsNodeNeeded(attrs)
        if addAttributeSet:
            attributeSetNode = self.createNode('AttributeSet', primPath=primSpec.path.pathString, primSpec=primSpec)
            self._addChildNode(attributeSetNode, upNode)
            upNode = attributeSetNode

        return upNode

    def _getPrimRelationships(self, primSpec, upNode):
        attrs = primSpec.relationships.keys()
        if len(attrs) == 0:
            return upNode

        addMaterialAssign = MaterialAssignNode._checkIsNodeNeeded(attrs)
        if addMaterialAssign:
            materialAssignNode = self.createNode('MaterialAssign', primPath=primSpec.path.pathString, primSpec=primSpec)
            self._addChildNode(materialAssignNode, upNode)
            upNode = materialAssignNode

        addRelationshipSet = RelationshipSetNode._checkIsNodeNeeded(attrs)
        if addRelationshipSet:
            relationshipSetNode = self.createNode('RelationshipSet', primPath=primSpec.path.pathString, primSpec=primSpec)
            self._addChildNode(relationshipSetNode, upNode)
            upNode = relationshipSetNode

        return upNode

    def _connectShadeNodeInputs(self, node):
        if not node.Class() in ['Shader', 'Material']:
            return
        for param in node.parameters():
            node.nodeObject.connectShader(param)

    def getPrimNode(self, primPath):
        nodes = self._primNodes.get(primPath)
        if nodes is not None:
            return nodes[0]

    def getRootNode(self):
        nodes = self.getNodes(type='Root')
        if len(nodes) == 0:
            return
        return nodes[0]

    def _connectShadeNodes(self):
        for node in self.getNodes(type=['Shader', 'Material']):
            self._connectShadeNodeInputs(node)

    def _layoutNode(self, node):
        childrenCount = 0
        for index, child in enumerate(node.getDestinations()):
            child.setX(childrenCount * (node.w + 50) + node.pos().x())
            currentChildCount = self._layoutNode(child)
            if currentChildCount > 1:
                childrenCount += currentChildCount
            else:
                childrenCount += 1
        return childrenCount

    def layoutNodes(self):
        node = self.getRootNode()
        self._layoutNode(node)
        for node in self.allNodes():
            node.updatePipe()

    def _afterNodeNameChanged(self, node):
        self._allNodes[node] = node.name()

    def _getUniqueName(self, name):
        # nodes = self.allNodes()
        # names = [n.name() for n in nodes]
        names = self._allNodes.values()

        match = re.match(NODE_NAME_PATTERN, name)
        if match:
            suffix = match.group('suffix')
            index = int(match.group('index'))
        else:
            suffix = name
            index = 0

        if name not in names:
            return name, suffix, index

        if suffix in self._nodesSuffix:
            indexs = self._nodesSuffix.get(suffix)
            indexs.sort(reverse=True)
        else:
            indexs = []

        if len(indexs) > 0:
            index = indexs[0]

        while name in names:
            index += 1
            name = '{}{}'.format(suffix, index)

        return name, suffix, index

    def _executeLayerNodes(self, stage, nodes):
        nodes.sort(lambda n1,n2: cmp(n1.pos().y(),n2.pos().y()))
        for node in nodes:
            stage, _ = node.execute(stage, None)

        return stage

    def _executeNode(self, node, stage, prim):
        stage, prim = node.execute(stage, prim)
        if node.Class() == 'VariantSwitch':
            variantSet = node.nodeObject.getVariantSet(prim)
            variantSelected = node.nodeObject.getVariantSelection()

            currentSelected = variantSet.GetVariantSelection()

            variantSet.SetVariantSelection(variantSelected)
            with variantSet.GetVariantEditContext():
                for child in node.getDestinations():
                    stage = self._executeNode(child, stage, prim)

            variantSet.SetVariantSelection(currentSelected)
        else:
            for child in node.getDestinations():
                stage = self._executeNode(child, stage, prim)

        return stage

    def _executeAllToStage(self):
        stage = Usd.Stage.CreateInMemory()
        prim = None

        layerNodes = self.getNodes(type='Layer')
        stage = self._executeLayerNodes(stage, layerNodes)

        node = self.getRootNode()
        stage = self._executeNode(node, stage, prim)

        return stage

    def setStage(self, stage, layer=None, assetPath=None, reset=True):
        self.stage = stage
        if layer is None:
            layer = stage.GetRootLayer()
        self.layer = layer
        self.assetPath = assetPath
        self.editable = isEditable(self.layer.realPath)

        if reset:
            ungFile = os.path.splitext(self.layer.realPath)[0] + '.ung'
            if os.path.exists(ungFile):
                self.loadSceneFromUng(ungFile)
            else:
                self.loadSceneFromLayer()

    def reloadLayer(self):
        self.resetScene()

    def clear(self):
        for node in self.allNodes():
            self.deleteNode(node)
        super(GraphicsScene, self).clear()

    def _loadSceneFromUng(self, ungFile):
        self.view._floatWidget.switchButton.setFormat('ung')

        with open(ungFile, 'r') as f:
            xmlString = f.read()
        with GraphState.stopLiveUpdate():
            self.pasteNodesFromXml(xmlString, selected=False)
        # self.applyChanges()

    def _loadSceneFromXml(self, xmlString):
        self.view._floatWidget.switchButton.setFormat('ung')

        with GraphState.stopLiveUpdate():
            self.pasteNodesFromXml(xmlString, selected=False)
        # self.applyChanges()

    @log_cost_time
    def resetScene(self, forceFromLayer=False, xmlString=''):
        self._beforeResetScene()

        ungFile = os.path.splitext(self.layer.realPath)[0] + '.ung'
        if forceFromLayer:
            self._loadSceneFromLayer()
        elif xmlString != '':
            self._loadSceneFromXml(xmlString)
        elif os.path.exists(ungFile):
            self._loadSceneFromUng(ungFile)
        else:
            self._loadSceneFromLayer()

        self._afterResetScene()

    def _beforeResetScene(self):
        self.clear()
        self._primNodes = {}
        self._allNodes = {}
        self._nodesSuffix = {}

    def _afterResetScene(self):
        self.view._resizeScene()
        self.frameSelection()

        logger.debug('scene nodeItem number: {}'.format(len(self.allNodes())))

    def _loadSceneFromLayer(self):
        with GraphState.stopLiveUpdate():
            self.view._floatWidget.switchButton.setFormat('usd')

            primSpec = self.layer.GetPrimAtPath('/')

            rootNode = self.createNode('Root')
            self._addNodeToPrimPath(rootNode, '/')

            self._addLayerNodes(self.layer)
            self._getIntoPrim(primSpec, rootNode)

            # we need to connect shader nodes after all nodes are created
            self._connectShadeNodes()

            self.layoutNodes()

    def createNode(self, nodeClass, name=None, primPath=None, pos=None, **kwargs):
        # QCoreApplication.processEvents()

        if nodeClass in Node.getAllNodeClassNames():
            if name is None:
                name = nodeClass
            nodeName, suffix, index = self._getUniqueName(name)
            nodeItem = NodeItem.createItem(
                nodeClass,
                stage=self.stage, layer=self.layer,
                name=nodeName, primPath=primPath,
                **kwargs
            )

            self.addItem(nodeItem)
            nodeItem.afterAddToScene()
            self._allNodes.update({nodeItem: nodeName})

            if pos is None:
                center = self.view.getCenterPos()
                pos = [center.x(), center.y()]
            nodeItem.setX(pos[0])
            nodeItem.setY(pos[1])

            if suffix in self._nodesSuffix:
                self._nodesSuffix[suffix].append(index)
            else:
                self._nodesSuffix[suffix] = [index]

            return nodeItem

    def connectAsChild(self, node, parentNode):
        self._addChildNode(node, parentNode)

    def selectAll(self):
        for node in self.allNodes():
            node.setSelected(True)

    def deleteSelection(self):
        with GraphState.stopLiveUpdate():
            self._deleteSelection()
        self.liveUpdateRequired()

    def _deleteSelection(self):
        selectedPipes = []
        selectedNodes = []
        for item in self.selectedItems():
            if isinstance(item, NodeItem):
                selectedNodes.append(item)
            elif isinstance(item, Pipe):
                selectedPipes.append(item)

        for pipe in selectedPipes:
            pipe.breakConnection()

        for node in selectedNodes:
            self.deleteNode(node)

    def deleteNode(self, node):
        pipes = []
        for port in node.ports:
            for pipe in port.pipes:
                if pipe not in pipes:
                    pipes.append(pipe)
        for pipe in pipes:
            pipe.breakConnection()
        self.removeItem(node)
        self._allNodes.pop(node)
        self.nodeDeleted.emit(node)

    def frameSelection(self):
        self.view.fitTo(self.selectedItems())

    def disableSelection(self):
        for node in self.getSelectedNodes():
            node.parameter('disable').setValue(1 - node.parameter('disable').getValue())
        self.liveUpdateRequired()

    def enterSelection(self, force=False):
        for item in self.selectedItems():
            if item.nodeObject.Class() == 'Layer':
                self.enterLayerRequired.emit(item.parameter('layerPath').getValue(), force)
                return
            elif item.nodeObject.Class() in ['Reference', 'Payload']:
                self.enterFileRequired.emit(item.parameter('assetPath').getValue(), force)
                return

    def forceEnterSelection(self):
        self.enterSelection(force=True)

    def updateSelectedNodesPipe(self):
        pipes = []
        for node in self.getSelectedNodes():
            for port in node.ports:
                for pipe in port.pipes:
                    if pipe not in pipes:
                        pipes.append(pipe)
        for pipe in pipes:
            pipe.updatePath()

    def allNodes(self):
        return self._allNodes.keys()
        # nodes = [item for item in self.items() if isinstance(item, NodeItem)]
        # return nodes

    def getNode(self, nodeName):
        nodes = self.allNodes()
        for node in nodes:
            if node.name() == nodeName:
                return node

    def getNodes(self, type=None):
        nodes = self.allNodes()
        if type is None:
            return nodes
        if not isinstance(type, (list, tuple)):
            type = [type]
        nodes = [n for n in nodes if n.nodeType in type]
        return nodes

    def getSelectedNodes(self):
        return [n for n in self.selectedItems() if isinstance(n, NodeItem)]

    def getNodesAsXml(self, nodes):
        rootElement = ET.Element('usdnodegraph')
        nodesDict = {}
        if len(nodes) > 0:
            firstNode = nodes[0]
            minX = firstNode.parameter('x').getValue()
            minY = firstNode.parameter('y').getValue()
            for node in nodes:
                nodeElement = node.toXmlElement()
                rootElement.append(nodeElement)

                minX = min(node.parameter('x').getValue(), minX)
                minY = min(node.parameter('y').getValue(), minY)

            rootElement.set('x', str(minX))
            rootElement.set('y', str(minY))
            nodesString = convertToString(rootElement)
            return nodesString
        return ''

    def _exportNodesToFile(self, nodes, xmlfile):
        nodesString = self.getNodesAsXml(nodes)
        with open(xmlfile, 'w') as f:
            f.write(nodesString)

    def getSelectedNodesAsXml(self):
        nodes = self.getSelectedNodes()
        return self.getNodesAsXml(nodes)

    def getAllNodesAsXml(self):
        nodes = self.allNodes()
        return self.getNodesAsXml(nodes)

    def exportAllNodesToFile(self, xmlfile):
        nodes = self.allNodes()
        self._exportNodesToFile(nodes, xmlfile)

    def exportSelectedNodesToFile(self, xmlfile):
        nodes = self.getSelectedNodes()
        self._exportNodesToFile(nodes, xmlfile)

    def createParamFromXml(self, paramElement, node, offsetX=0, offsetY=0):
        paramName = paramElement.get('n')
        if paramName in ['name']:
            return

        custom = paramElement.get('cus', '0')
        visible = paramElement.get('vis', '1')
        parameterType = paramElement.get('t')
        value = paramElement.get('val')
        connect = paramElement.get('con')
        samples = paramElement.findall('s')
        metadatas = paramElement.findall('m')
        hints = paramElement.findall('h')

        timeSamples = {}

        if node.hasParameter(paramName):
            parameter = node.parameter(paramName)
        else:
            parameter = node.addParameter(paramName, parameterType, custom=custom)

        if connect is not None:
            parameter.setConnect(connect)
        if len(samples) == 0:
            value = parameter.convertValueFromPy(value)
            if paramName == 'x':
                value = offsetX + value
                node.setX(value)
            elif paramName == 'y':
                value = offsetY + value
                node.setY(value)
            parameter.setValueQuietly(value)
        else:
            for sampleElement in samples:
                time = float(sampleElement.get('t'))
                value = sampleElement.get('v')
                timeSamples[time] = parameter.convertValueFromPy(value)
            parameter.setTimeSamplesQuietly(timeSamples)

        for metadataElement in metadatas:
            self.createMetadataFromXml(metadataElement, parameter)
        for hintElement in hints:
            self.createHintFromXml(hintElement, parameter)

    def createMetadataFromXml(self, metadataElement, obj):
        key = metadataElement.get('k')
        value = metadataElement.get('v')
        obj.setMetadata(key, value)

    def createHintFromXml(self, hintElement, obj):
        key = hintElement.get('k')
        value = hintElement.get('v')
        obj.setHint(key, value)

    def createNodeFromXml(self, nodeElement, _newNodes, _nameConvertDict, offsetX=0, offsetY=0):
        oldNodeName = nodeElement.get('n')
        nodeClass = nodeElement.get('c')
        node = self.createNode(nodeClass, name=oldNodeName)
        newName = node.parameter('name').getValue()

        _newNodes.append(node)
        _nameConvertDict.update({oldNodeName: newName})

        for paramElement in nodeElement.findall('p'):
            self.createParamFromXml(paramElement, node, offsetX, offsetY)

        for metadataElement in nodeElement.findall('m'):
            self.createMetadataFromXml(metadataElement, node)

        node.afterAddToScene()

    def createConnectFromXml(self, nodeElement, _nameConvertDict):
        oldNodeName = nodeElement.get('n')

        newNode = self.getNode(_nameConvertDict.get(oldNodeName))
        if newNode is None:
            return

        for outputElement in nodeElement.findall('o'):
            outputName = outputElement.get('n')
            sourceNodeName = outputElement.get('conN')
            sourceNodeInputName = outputElement.get('conP')

            sourceNode = self.getNode(_nameConvertDict.get(sourceNodeName))
            if sourceNode is None:
                sourceNode = self.getNode(sourceNodeName)
                if sourceNode is None:
                    continue
            sourceNode.connectSource(newNode, inputName=sourceNodeInputName, outputName=outputName)

        for inputElement in nodeElement.findall('i'):
            inputName = inputElement.get('n')
            sourceNodeName = inputElement.get('conN')
            sourceNodeOutputName = inputElement.get('conP')

            sourceNode = self.getNode(_nameConvertDict.get(sourceNodeName))
            if sourceNode is None:
                sourceNode = self.getNode(sourceNodeName)
                if sourceNode is None:
                    continue
            newNode.connectSource(sourceNode, inputName=inputName, outputName=sourceNodeOutputName)

    def createNodesFromXml(self, rootElement, offsetX=0, offsetY=0):
        _nameConvertDict = {}
        _newNodes = []
        for nodeElement in rootElement.getchildren():
            self.createNodeFromXml(
                nodeElement, _newNodes, _nameConvertDict,
                offsetX, offsetY
            )

        # connections
        for nodeElement in rootElement.getchildren():
            self.createConnectFromXml(nodeElement, _nameConvertDict)

        return _newNodes

    def pasteNodesFromXml(self, nodesString, selected=True):
        rootElement = ET.fromstring(nodesString)
        _topLeftX = float(rootElement.get('x'))
        _topLeftY = float(rootElement.get('y'))

        scenePos = self.view.mapToScene(self.view.clickedPos)
        offsetX = scenePos.x() - _topLeftX
        offsetY = scenePos.y() - _topLeftY

        nodes = self.createNodesFromXml(rootElement, offsetX, offsetY)
        if selected:
            for node in nodes:
                node.setSelected(True)

        return nodes

    def exportToString(self):
        stage = self._executeAllToStage()
        return stage.GetRootLayer().ExportToString()

    def _exportToFile(self, exportFile):
        if not self.editable:
            QtWidgets.QMessageBox.warning(None, 'Warning', 'This layer can\'t be exported!')
            return
        stage = self._executeAllToStage()
        print exportFile
        stage.GetRootLayer().Export(exportFile)

    def exportToFile(self):
        # save to another file
        usdFile = self.layer.realPath

        exportFile = usdFile
        exportExt = os.path.splitext(usdFile)[-1]
        exportFile = usdFile.replace(exportExt, '_export' + exportExt)

        self._exportToFile(exportFile)

    def saveLayer(self):
        usdFile = self.layer.realPath
        self._exportToFile(usdFile)

    def saveNodes(self):
        usdFile = self.layer.realPath
        xmlFile = os.path.splitext(usdFile)[0] + '.ung'
        self.exportAllNodesToFile(xmlFile)

    def applyChanges(self):
        stage = self._executeAllToStage()

        layerString = stage.GetRootLayer().ExportToString()
        self.layer.ImportFromString(layerString)

        GraphState.executeCallbacks(
            'layerChangesApplied',
            layer=self.layer.realPath
        )

    def liveUpdateRequired(self):
        if GraphState.isLiveUpdate():
            self.applyChanges()

    def setAsEditTarget(self):
        if self.stage is not None:
            self.stage.SetEditTarget(self.layer)

    def _addNodeToPrimPath(self, nodeItem, path):
        if path not in self._primNodes:
            self._primNodes[path] = []
        self._primNodes[path].append(nodeItem)

    def reSyncPath(self, node, parentPaths=None):
        node.reSyncPath(parentPaths)
        syncPaths = node.getPrimPath()
        for syncPath in syncPaths:
            self._addNodeToPrimPath(node.item, syncPath)

        for n in [i.nodeObject for i in node.item.getDestinations()]:
            self.reSyncPath(n, syncPaths)

    def reSyncPaths(self):
        self._primNodes = {}
        self.reSyncPath(self.rootNode.nodeObject)

    def findNodeAtPath(self, path):
        self.reSyncPaths()

        find = False
        findPath = path
        findNodes = []
        while not find:
            for key, nodes in self._primNodes.items():
                node = nodes[0]
                sdfPath = Sdf.Path(key)
                composedPath = sdfPath.StripAllVariantSelections()
                # print key, composedPath
                if composedPath == findPath:
                    findNodes.append(node)
                    find = True
            if not find:
                findPath = '/'.join(findPath.split('/')[:-1])
                if findPath == '':
                    findPath = '/'

        self.clearSelection()

        primPath = findPath
        addPath = path.replace(findPath, '')
        addPrimNames = addPath.split('/')
        for findNode in findNodes:
            currentNode = findNode
            for addPrimName in addPrimNames:
                if addPrimName == '':
                    continue

                primPath += '/' + addPrimName

                node = self.createNode('PrimOverride')
                node.parameter('primName').setValue(addPrimName)
                self._addChildNode(node, currentNode)
                self._addNodeToPrimPath(node, primPath)
                currentNode = node

            currentNode.setSelected(True)

        self.layoutNodes()
        self._layoutNode(findNode)

        self.frameSelection()

        selected = self.selectedItems()
        return selected

