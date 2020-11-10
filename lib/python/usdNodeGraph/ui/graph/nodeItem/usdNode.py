# -*- coding: utf-8 -*-

from usdNodeGraph.module.sqt import QtWidgets
from .nodeItem import NodeItem


class UsdNodeItem(NodeItem):
    nodeItemType = 'UsdNodeItem'

    def getToolTip(self):
        tooltip = super(UsdNodeItem, self).getToolTip()
        tooltip += '\n'
        tooltip += '\n'.join(self.nodeObject.getPrimPath())
        return tooltip

    def execute(self, stage, prim):
        return self.nodeObject.execute(stage, prim)

    def getPrimPath(self):
        return self.nodeObject.getPrimPath()

    def getContextMenus(self):
        menus = super(UsdNodeItem, self).getContextMenus()
        menus.extend([
            ['copy_path', 'Copy Prim Path', None, self._copyPathActionTriggered],
        ])
        return menus

    def _copyPathActionTriggered(self):
        path = ' + '.join(self.nodeObject.getPrimPath())
        cb = QtWidgets.QApplication.clipboard()
        cb.setText(path)


NodeItem.registerNodeItem(UsdNodeItem)

