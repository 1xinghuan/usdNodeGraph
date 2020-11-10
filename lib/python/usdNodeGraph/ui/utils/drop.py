# -*- coding: utf-8 -*-

from usdNodeGraph.module.sqt import QtWidgets, QtCore


class DropWidget(QtWidgets.QWidget):
    filesDroped = QtCore.Signal(list)

    def __init__(self):
        # super(DropWidget, self).__init__()

        self.acceptFileExts = None
        self.dropLabel = None
        self.setAcceptDrops(True)

    def addDropLabel(self):
        self.dropLabel = QtWidgets.QLabel(self)
        self.dropLabel.setText('Drop Files Here')
        self.dropLabel.setVisible(False)
        self.dropLabel.setAlignment(QtCore.Qt.AlignCenter)

    def setAcceptExts(self, exts):
        if not isinstance(exts, list):
            exts = [exts]
        self.acceptFileExts = exts

    def getAcceptFiles(self, event):
        files = []
        for url in event.mimeData().urls():
            f = str(url.toLocalFile())
            if self.acceptFileExts is None or f.endswith(tuple(self.acceptFileExts)):
                files.append(f)
        return files

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            files = self.getAcceptFiles(event)
            if len(files) > 0:
                if self.dropLabel is not None:
                    self.dropLabel.setVisible(True)
                    self.dropLabel.move(0, 0)
                    self.dropLabel.resize(self.width(), self.height())
                event.accept()
            else:
                super(DropWidget, self).dragEnterEvent(event)
        else:
            super(DropWidget, self).dragEnterEvent(event)

    def dragLeaveEvent(self, event):
        if self.dropLabel is not None:
            self.dropLabel.setVisible(False)
        # super(DropWidget, self).dragLeaveEvent(event)

    def dragMoveEvent(self, event):
        super(DropWidget, self).dragMoveEvent(event)

    def dropEvent(self, event):
        if self.dropLabel is not None:
            self.dropLabel.setVisible(False)
        if event.mimeData().hasUrls():
            acceptFiles = self.getAcceptFiles(event)
            self.afterFilesDrop(acceptFiles)
        else:
            super(DropWidget, self).dropEvent(event)

    def afterFilesDrop(self, acceptFiles):
        pass



