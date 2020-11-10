from usdNodeGraph.module.sqt import QtWidgets, QtGui, QtCore


class WithMenuObject(object):
    _actionShortCutMap = {}

    @classmethod
    def registerActionShortCut(cls, actionName, shortCut):
        cls._actionShortCutMap.update({
            actionName: shortCut
        })

    def _addSubMenus(self, menu, menus):
        for menuL in menus:
            name = menuL[0]

            if name == 'separater':
                menu.addSeparator()
                continue

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

    def _addAction(self, name, label, menu, shortCut=None, triggerFunc=None):
        action = QtWidgets.QAction(label, menu)
        action.setObjectName(name)
        menu.addAction(action)
        if name in self._actionShortCutMap:
            shortCut = self._actionShortCutMap.get(name)
        if shortCut is not None:
            action.setShortcut(shortCut)
        if triggerFunc is not None:
            action.triggered.connect(triggerFunc)

