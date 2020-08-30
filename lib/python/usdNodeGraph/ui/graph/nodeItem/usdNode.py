# -*- coding: utf-8 -*-
# __author__ = 'XingHuan'


from usdNodeGraph.ui.graph.nodeItem.nodeItem import NodeItem


class UsdNodeItem(NodeItem):
    nodeItemType = 'UsdNodeItem'

    def execute(self, stage, prim):
        return self.nodeObject.execute(stage, prim)


NodeItem.registerNodeItem(UsdNodeItem)

