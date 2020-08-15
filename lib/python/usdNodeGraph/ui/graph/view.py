# -*- coding: utf-8 -*-
# __author__ = 'XingHuan'
# 8/29/2018

import os
import re
import json
import time
from pxr import Usd, Sdf, Ar
from usdNodeGraph.module.sqt import *
from usdNodeGraph.utils.const import INPUT_ATTRIBUTE_PREFIX, OUTPUT_ATTRIBUTE_PREFIX, VIEWPORT_FULL_UPDATE
from .node import (
    Node, NodeItem, LayerNode, ReferenceNode, PayloadNode,
    TransformNode, AttributeSetNode)
from .pipe import Pipe
from .node.port import Port
from usdNodeGraph.utils.log import get_logger, log_cost_time


logger = get_logger('usdNodeGraph.view')


NODE_NAME_PATTERN = re.compile('(?P<suffix>[^\d]*)(?P<index>\d+)')
VARIANT_PRIM_PATH_PATTERN = re.compile('.*{(?P<variantSet>.+)=(?P<variant>.+)}$')

VIEW_FILL_COLOR = QtGui.QColor(38, 38, 38)
VIEW_LINE_COLOR = QtGui.QColor(55, 55, 55)
VIEW_CENTER_LINE_COLOR = QtGui.QColor(80, 80, 60, 50)
VIEW_GRID_WIDTH = 200
VIEW_GRID_HEIGHT = 100

VIEW_ZOOM_STEP = 1.1


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

    def setVisible(self, bool):
        super(FloatLineEdit, self).setVisible(bool)
        if bool:
            self._edit.setFocus()


class GraphicsView(QtWidgets.QGraphicsView):
    def __init__(self, *args, **kwargs):
        super(GraphicsView, self).__init__(*args, **kwargs)

        self.currentZoom = 1.0
        self.panningMult = 2.0 * self.currentZoom
        self.panning = False
        self.keyZooming = False
        self.clickedPos = QtCore.QPointF(0, 0)

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

        self._createNewFloatEdit.editFinished.connect(self._floatEditFinished)

    def _zoom(self, zoom):
        self.scale(zoom, zoom)
        self.currentZoom = self.transform().m11()
        self._resizeScene()

    def _resizeScene(self, setLabel=True):
        center_x = self.mapToScene(QtCore.QPoint(self.viewport().width() / 2, self.viewport().height() / 2)).x()
        center_y = self.mapToScene(QtCore.QPoint(self.viewport().width() / 2, self.viewport().height() / 2)).y()
        w = self.viewport().width() / self.currentZoom * 2 + 25000
        h = self.viewport().height() / self.currentZoom * 2 + 25000

        self.scene().setSceneRect(QtCore.QRectF(
            center_x - w / 2,
            center_y - h / 2,
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

        point1 = self.mapToScene(QtCore.QPoint(0, 0))
        point2 = self.mapToScene(QtCore.QPoint(self.viewport().width(), self.viewport().height()))
        rect = QtCore.QRectF(point1, point2)

        for node in self.scene().allNodes():
            if rect.contains(node.pos()):
                node.setLabelVisible(showNodeLabel)
                node.setPortsLabelVisible(showPortLabel)

    def focusNextPrevChild(self, bool):
        return False

    # def keyPressEvent(self, event):
    #     super(GraphicsView, self).keyPressEvent(event)
    #     if event.key() == QtCore.Qt.Key_Tab:
    #         self.showFloatEdit()
    #     # elif event.key() == QtCore.Qt.Key_Delete:
    #     #     self.scene().deleteSelection()

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
        # self.clickedPos = event.pos()

        if self.panning:
            if event.button() == QtCore.Qt.LeftButton:
                self.keyZooming = True
                self.panning = False
                self.setCursor(QtCore.Qt.ArrowCursor)
                return

        if event.button() == QtCore.Qt.MiddleButton:
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
            self.panning = True
            self.prevPos = event.pos()
            self.prevCenter = self.mapToScene(QtCore.QPoint(self.viewport().width() / 2, self.viewport().height() / 2))
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
            if mouseMoveY < 0: #  zoom in
                zoom = -mouseMoveY * 0.01 + 1
                self._zoom(zoom)
            elif mouseMoveY > 0:
                zoom = 1.0 / (mouseMoveY * 0.01 + 1)
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

    def drawBackground(self, painter, rect):
        painter.setBrush(QtGui.QBrush(VIEW_FILL_COLOR))
        painter.setPen(QtGui.QPen(VIEW_LINE_COLOR))

        painter.drawRect(rect)
        lines = []
        scale = max(int(1 / self.currentZoom / 2), 1)
        line_w = VIEW_GRID_WIDTH * scale
        line_h = VIEW_GRID_HEIGHT * scale

        point1 = self.mapToScene(QtCore.QPoint(0, 0))
        point2 = self.mapToScene(QtCore.QPoint(self.viewport().width(), self.viewport().height()))

        # for i in range(int(point1.y() / line_h), int(self.scene().height() / line_h)):
        for i in range(int(point1.y() / line_h), int(point2.y() / line_h) + 1):
            lines.append(QtCore.QLineF(
                QtCore.QPoint(rect.x(), i * line_h),
                QtCore.QPoint(rect.x() + rect.width(), i * line_h)))
        # for i in range(int(self.scene().sceneRect().x()), int(self.scene().width() / line_w)):
        for i in range(int(point1.x() / line_w), int(point2.x() / line_w) + 1):
            lines.append(QtCore.QLineF(
                QtCore.QPoint(i * line_w, rect.y()),
                QtCore.QPoint(i * line_w, rect.y() + rect.height())))
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
        node = self.scene().createNode(text)
        if node is not None:
            scenePos = self.mapToScene(self.clickedPos)
            node.setX(scenePos.x())
            node.setY(scenePos.y())


class GraphicsSceneWidget(QtWidgets.QWidget):
    itemDoubleClicked = QtCore.Signal(object)
    showWidgetSignal = QtCore.Signal(int)
    enterFileRequired = QtCore.Signal(str)
    enterLayerRequired = QtCore.Signal(object, object)

    def __init__(self, parent=None):
        super(GraphicsSceneWidget, self).__init__(parent=parent)

        self.stage = None
        self.layer = None

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

    def _enterFileRequired(self, usdFile):
        # for Reference and Payload
        absLayerPath = self._getAbsPath(usdFile)
        self.enterFileRequired.emit(absLayerPath)

    def _enterLayerRequired(self, layerPath):
        # for sublayer
        absLayerPath = self._getAbsPath(layerPath)
        layer = Sdf.Layer.FindOrOpen(absLayerPath)
        self.enterLayerRequired.emit(self.stage, layer)

    def setStage(self, stage, layer=None, reset=True):
        self.stage = stage
        if layer is None:
            layer = stage.GetRootLayer()
        self.layer = layer
        self.scene.setStage(self.stage, self.layer, reset=reset)

    def exportToString(self):
        return self.scene.exportToString()

    def exportToFile(self):
        self.scene.exportToFile()

    def applyChanges(self):
        self.scene.applyChanges()


class GraphicsScene(QtWidgets.QGraphicsScene):
    enterFileRequired = QtCore.Signal(str)
    enterLayerRequired = QtCore.Signal(str)
    nodeParameterChanged = QtCore.Signal(object)

    def __init__(self, view=None, **kwargs):
        super(GraphicsScene, self).__init__(**kwargs)

        self.view = view

        self.stage = None
        self.layer = None

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

    def _getPrim(self, primSpec, upNode=None, index=0):
        skipAttribute = False

        primPath = primSpec.path.pathString
        match = re.match(VARIANT_PRIM_PATH_PATTERN, primPath)
        if match:
            variantSwitchNode = self.createNode(
                'VariantSwitch', primPath=primPath,
                variantSetName=match.group('variantSet'),
                variantSelected=match.group('variant')
            )
            self._addChildNode(variantSwitchNode, upNode, index=index)
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
                else:
                    primNode = self.createNode('PrimDefine', primPath=primPath, primSpec=primSpec)
            elif specifier == Sdf.SpecifierOver:
                primNode = self.createNode('PrimOverride', primPath=primPath, primSpec=primSpec)
            else:
                return upNode

            self._addChildNode(primNode, upNode, index=index)
            self._primNodes.update({primPath: primNode})
            upNode = primNode

        # reference
        referenceList = primSpec.referenceList.GetAddedOrExplicitItems()
        for reference in referenceList:
            referenceNode = self.createNode('Reference', primPath=primPath, reference=reference)
            self._addChildNode(referenceNode, upNode)

            upNode = referenceNode

        # payload
        payloadList = primSpec.payloadList.GetAddedOrExplicitItems()
        for payload in payloadList:
            payloadNode = self.createNode('Payload', primPath=primPath, payload=payload)
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
                variantSetNode = self.createNode('VariantSet', primPath=primPath, variantSet=variantSetSpec)
                self._addChildNode(variantSetNode, upNode)

                variantSelected = variantSelections.get(variantSetName)
                variantSelectNode = self.createNode(
                    'VariantSelect', primPath=primPath,
                    variantSetName=variantSetName,
                    variantSelected=variantSelected,
                    primSpec=primSpec
                )
                self._addChildNode(variantSelectNode, variantSetNode)
                selectedVariantDict.update({variantSetName: variantSelected})

                variantList = variantSetSpec.variantList
                for i, variantSpec in enumerate(variantList):
                    variantPrim = variantSpec.primSpec
                    self._getIntoPrim(variantPrim, upNode=variantSelectNode, index=i)

        for variantSetName, variantSelected in variantSelections.items():
            if not variantSetName in selectedVariantDict:
                variantSelectNode = self.createNode(
                    'VariantSelect', primPath=primPath,
                    variantSetName=variantSetName,
                    variantSelected=variantSelected,
                    primSpec=primSpec
                )
                self._addChildNode(variantSelectNode, upNode)
                upNode = variantSelectNode

        return upNode

    def _getIntoPrim(self, primSpec, upNode, index=0):
        childrenCount = 0

        primPath = primSpec.path.pathString
        node = upNode
        if primPath != '/':
            node = self._getPrim(primSpec, upNode, index)
        for childName, child in primSpec.nameChildren.items():
            currentChildCount = self._getIntoPrim(child, node, childrenCount)
            if currentChildCount > 1:
                childrenCount += currentChildCount
            else:
                childrenCount += 1

        return childrenCount

    def _getPrimAttributes(self, primSpec, upNode, index=0):
        attrs = primSpec.attributes.keys()
        if len(attrs) == 0:
            return upNode

        addTransform = TransformNode._checkIsNodeNeeded(attrs)
        if addTransform:
            transformNode = self.createNode('Transform', primPath=primSpec.path.pathString, primSpec=primSpec)
            self._addChildNode(transformNode, upNode, index=index)
            upNode = transformNode

        addAttributeSet = AttributeSetNode._checkIsNodeNeeded(attrs)
        if addAttributeSet:
            attributeSetNode = self.createNode('AttributeSet', primPath=primSpec.path.pathString, primSpec=primSpec)
            self._addChildNode(attributeSetNode, upNode, index=index)
            upNode = attributeSetNode

        return upNode

    def _getPrimRelationships(self, primSpec, upNode, index=0):
        if len(primSpec.relationships.keys()) == 0:
            return upNode

        if 'material:binding' in primSpec.relationships.keys():
            relationship = primSpec.relationships.get('material:binding')
            material = relationship.targetPathList.GetAddedOrExplicitItems()[0].pathString
            materialAssignNode = self.createNode('MaterialAssign', primPath=primSpec.path.pathString, material=material)
            self._addChildNode(materialAssignNode, upNode, index=index)
            upNode = materialAssignNode

            if len(primSpec.relationships.keys()) == 1:  # only material:binding
                return upNode

        relationshipSetNode = self.createNode('RelationshipSet', primPath=primSpec.path.pathString, primSpec=primSpec)
        self._addChildNode(relationshipSetNode, upNode, index=index)
        upNode = relationshipSetNode

        return upNode

    def _connectShadeNodeInputs(self, node):
        if not node.Class() in ['Shader', 'Material']:
            return
        for param in node.parameters():
            node.nodeObject.connectShader(param)

    def getPrimNode(self, primPath):
        return self._primNodes.get(primPath)

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

    def _layoutNodes(self):
        node = self.rootNode
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
            with variantSet.GetVariantEditContext():
                for child in node.getDestinations():
                    stage = self._executeNode(child, stage, prim)
        else:
            for child in node.getDestinations():
                stage = self._executeNode(child, stage, prim)

        return stage

    def _executeAllToStage(self):
        stage = Usd.Stage.CreateInMemory()
        prim = None

        layerNodes = self.getNodes(type='Layer')
        stage = self._executeLayerNodes(stage, layerNodes)

        node = self.rootNode
        stage = self._executeNode(node, stage, prim)

        return stage

    def setStage(self, stage, layer=None, reset=True):
        self.stage = stage
        if layer is None:
            layer = stage.GetRootLayer()
        self.layer = layer

        if reset:
            self.resetScene()

    def reloadLayer(self):
        self.resetScene()

    @log_cost_time
    def resetScene(self):
        self.clear()
        self._primNodes = {}
        self._allNodes = {}
        self._nodesSuffix = {}

        t = time.time()

        primSpec = self.layer.GetPrimAtPath('/')

        self.rootNode = self.createNode('Root')

        self._addLayerNodes(self.layer)
        self._getIntoPrim(primSpec, self.rootNode)

        # we need to connect shader nodes after all nodes are created
        self._connectShadeNodes()

        # self._layoutNodes()

        self.view._resizeScene()
        self.frameSelection()

        # logger.debug('resetScene time: {}'.format(time.time() - t))
        logger.debug('scene node number: {}'.format(len(self.allNodes())))

    def createNode(self, nodeClass, name=None, primPath=None, **kwargs):
        # QCoreApplication.processEvents()

        if nodeClass in Node.getAllNodeClassNames():
            if name is None:
                name = nodeClass
            nodeName, suffix, index = self._getUniqueName(name)
            nodeItem = Node.createItem(
                nodeClass,
                stage=self.stage, layer=self.layer,
                name=nodeName, primPath=primPath,
                **kwargs
            )
            # nodeItem.nodeObject.addPrimPath(primPath)

            self.addItem(nodeItem)
            nodeItem.afterAddToScene()
            self._allNodes.update({nodeItem: nodeName})

            if suffix in self._nodesSuffix:
                self._nodesSuffix[suffix].append(index)
            else:
                self._nodesSuffix[suffix] = [index]

            return nodeItem

    def selectAll(self):
        for node in self.allNodes():
            node.setSelected(True)

    def deleteSelection(self):
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
            for port in node.ports:
                for pipe in port.pipes:
                    pipe.breakConnection()

            self.removeItem(node)
            self._allNodes.pop(node)

    def frameSelection(self):
        self.view.fitTo(self.selectedItems())

    def disableSelection(self):
        for node in self.getSelectedNodes():
            node.parameter('disable').setValue(1 - node.parameter('disable').getValue())

    def enterSelection(self):
        for item in self.selectedItems():
            if isinstance(item.nodeObject, LayerNode):
                self.enterLayerRequired.emit(item.parameter('layerPath').getValue())
                return
            elif isinstance(item.nodeObject, (ReferenceNode, PayloadNode)):
                self.enterFileRequired.emit(item.parameter('assetPath').getValue())
                return

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

    def getSelectedNodesAsString(self):
        nodes = self.getSelectedNodes()
        nodesDict = {}
        if len(nodes) > 0:
            firstNode = nodes[0]
            minX = firstNode.parameter('x').getValue()
            minY = firstNode.parameter('y').getValue()
            for node in nodes:
                nodeData = node.toDict()
                nodesDict.update(nodeData)
                minX = min(node.parameter('x').getValue(), minX)
                minY = min(node.parameter('y').getValue(), minY)

            nodesDict.update({
                '_topLeftPos': [minX, minY]
            })
            nodesString = json.dumps(nodesDict, indent=4)
            return nodesString

    def pasteNodesFromString(self, nodesString):
        try:
            nodesDict = json.loads(nodesString)
        except:
            return
        _topLeftPos = nodesDict.get('_topLeftPos', [0, 0])
        nodesDict.pop('_topLeftPos')

        scenePos = self.view.mapToScene(self.view.clickedPos)
        offsetX = scenePos.x() - _topLeftPos[0]
        offsetY = scenePos.y() - _topLeftPos[1]

        _nameConvertDict = {}
        _newNodes = []

        # new nodes
        for oldNodeName, nodeDict in nodesDict.items():
            nodeClass = nodeDict.get('nodeClass')
            paramsDict = nodeDict.get('parameters', {})
            node = self.createNode(nodeClass, name=oldNodeName)
            _newNodes.append(node)
            newName = node.parameter('name').getValue()
            _nameConvertDict.update({oldNodeName: newName})

            for paramName, paramDict in paramsDict.items():
                if paramName in ['name']:
                    continue
                builtIn = paramDict.get('builtIn', False)
                parameterType = paramDict.get('parameterType')
                value = paramDict.get('value')
                timeSamples = paramDict.get('timeSamples')
                connect = paramDict.get('connect')

                if node.hasParameter(paramName):
                    parameter = node.parameter(paramName)
                else:
                    parameter = node.addParameter(paramName, parameterType)

                if connect is not None:
                    parameter.setConnect(connect)
                if timeSamples is None:
                    if paramName == 'x':
                        value = offsetX + value
                        node.setX(value)
                    elif paramName == 'y':
                        value = offsetY + value
                        node.setY(value)
                    value = parameter.convertValueFromPy(value)
                    parameter.setValueQuietly(value)
                else:
                    for key, value in timeSamples.items():
                        timeSamples[float(key)] = parameter.convertValueFromPy(value)
                    parameter.setTimeSamplesQuietly(timeSamples)

        # connections
        for oldNodeName, nodeDict in nodesDict.items():
            newNode = self.getNode(_nameConvertDict.get(oldNodeName))
            if newNode is None:
                continue

            inputsDict = nodeDict.get('inputs', {})
            # outputsDict = nodeDict.get('outputs', {})

            for inputName, [sourceNodeName, sourceNodeOutputName] in inputsDict.items():
                sourceNode = self.getNode(_nameConvertDict.get(sourceNodeName))
                if sourceNode is None:
                    sourceNode = self.getNode(sourceNodeName)
                    if sourceNode is None:
                        continue
                newNode.connectSource(sourceNode, inputName=inputName, outputName=sourceNodeOutputName)

            # self._connectShadeNodeInputs(newNode)

        for node in _newNodes:
            node.setSelected(True)
        return _newNodes

    def exportToString(self):
        stage = self._executeAllToStage()
        return stage.GetRootLayer().ExportToString()

    def exportToFile(self):
        stage = self._executeAllToStage()
        # stage.GetRootLayer().Save()

        # save to another file
        usdFile = self.layer.realPath

        exportFile = usdFile
        exportExt = os.path.splitext(usdFile)[-1]
        exportFile = usdFile.replace(exportExt, '_export' + exportExt)

        print exportFile
        print stage.GetRootLayer().ExportToString()
        stage.GetRootLayer().Export(exportFile)

    def applyChanges(self):
        stage = self._executeAllToStage()

        layerString = stage.GetRootLayer().ExportToString()
        self.layer.ImportFromString(layerString)

    def setAsEditTarget(self):
        if self.stage is not None:
            self.stage.SetEditTarget(self.layer)
