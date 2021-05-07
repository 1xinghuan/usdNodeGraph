# -*- coding: utf-8 -*-

from usdNodeGraph.module.sqt import QtWidgets, QtGui, QtCore


class MetadataPanel(QtWidgets.QTableWidget):
    def __init__(self):
        super(MetadataPanel, self).__init__()

        self.initUI()
        self.resetData()

        self.itemChanged.connect(self._itemChanged)

    def initUI(self):
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(['Key', 'Value'])
        self.setColumnWidth(1, 200)
        self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)

    def resetData(self):
        self.nodeOrParam = None
        self.metadatas = None

    def addMetadataItem(self, index, key, value):
        keyItem = QtWidgets.QTableWidgetItem(key)
        valueItem = QtWidgets.QTableWidgetItem(value)
        self.setItem(index, 0, keyItem)
        self.setItem(index, 1, valueItem)

    def setNodeOrParam(self, obj):
        self.resetData()
        self.nodeOrParam = obj
        self.metadatas = obj.getMetadatas()
        self.updateView()

    def updateView(self):
        self.itemChanged.disconnect(self._itemChanged)

        self.clearContents()

        keys = list(self.metadatas.keys())
        keys.sort()

        self.setRowCount(len(keys))
        for index, key in enumerate(keys):
            value = self.metadatas.get(key)
            self.addMetadataItem(index, key, value)

        self.itemChanged.connect(self._itemChanged)

    def _itemChanged(self, item):
        index = self.indexFromItem(item)
        row = index.row()

        key = str(self.item(row, 0).text())
        value = str(self.item(row, 1).text())

        self.nodeOrParam.setMetadata(key, value)

