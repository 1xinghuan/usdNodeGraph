# -*- coding: utf-8 -*-
# __author__ = 'XingHuan'


from pxr import Usd, Sdf, Kind, UsdGeom
from usdNodeGraph.module.sqt import *
from .node import NodeItem, registerNode, setNodeDefault, _BaseNodeItem
from .node import PixmapTag
from usdNodeGraph.ui.parameter.parameter import Parameter, StringParameter
from .port import InputPort, OutputPort


PORT_SPACING = 20


class UsdShaderNodeItem(_BaseNodeItem):
    nodeType = 'UsdShade'
    w = 150
    h = 450

    def __init__(self, *args, **kwargs):
        super(UsdShaderNodeItem, self).__init__(*args, **kwargs)
        self.orientation = 1

    def _initUI(self):
        super(UsdShaderNodeItem, self)._initUI()

    def _updateNameText(self, text):
        super(UsdShaderNodeItem, self)._updateNameText(text)
        rect = self.nameItem.boundingRect()
        self.nameItem.setX((self.w - rect.width()) / 2.0)
        self.nameItem.setY( - 10)

    def _updateUI(self):
        name = self.parameter('name').getValue()
        self._updateNameText(name)

    def addPort(self, port):
        super(UsdShaderNodeItem, self).addPort(port)

        index = self.ports.index(port)
        bbox = self.boundingRect()

        if isinstance(port, InputPort):
            port.setPos(
                bbox.left() - port.w / 2.0,
                15 + index * PORT_SPACING
            )
        else:
            port.setPos(
                bbox.right() - port.w + port.w / 2.0,
                bbox.height() - index * PORT_SPACING - 15
            )

    def addInputPort(self, portName):
        port = InputPort(portName)

        self.addPort(port)

    def addOutputPort(self, portName):
        port = OutputPort(portName)

        self.addPort(port)




















