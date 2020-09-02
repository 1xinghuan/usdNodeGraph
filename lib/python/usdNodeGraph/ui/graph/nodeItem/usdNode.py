# -*- coding: utf-8 -*-
# __author__ = 'XingHuan'

from usdNodeGraph.module.sqt import QtWidgets
from usdNodeGraph.ui.graph.nodeItem.nodeItem import NodeItem, LABEL_FONT


class UsdNodeItem(NodeItem):
    nodeItemType = 'UsdNodeItem'

    def getToolTip(self):
        tooltip = super(UsdNodeItem, self).getToolTip()
        tooltip += '\n'
        tooltip += '\n'.join(self.nodeObject.getPrimPath())
        return tooltip

    def execute(self, stage, prim):
        return self.nodeObject.execute(stage, prim)


NodeItem.registerNodeItem(UsdNodeItem)

