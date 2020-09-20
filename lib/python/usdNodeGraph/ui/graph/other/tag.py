# -*- coding: utf-8 -*-

from usdNodeGraph.module.sqt import QtWidgets, QtCore
from usdNodeGraph.utils.res import resource

TAG_W = 20
TAG_H = 20


class PixmapTag(QtWidgets.QGraphicsPixmapItem):
    w = TAG_W
    h = TAG_H

    def __init__(self, icon=None, **kwargs):
        super(PixmapTag, self).__init__(**kwargs)

        self.setAcceptHoverEvents(True)

        self.scaleFactor = 10
        self.icon = icon
        self.autoHide = True

        self._setPixmap()

    def _setPixmap(self, color=None):
        self.setPixmap(resource.get_pixmap(
            'icon',
            self.icon,
            color=color,
            scale=QtCore.QSize(TAG_W * self.scaleFactor, TAG_H * self.scaleFactor)
        ))
        self.setScale(1.0 / self.scaleFactor)


class LockTag(PixmapTag):
    def __init__(self, **kwargs):
        super(LockTag, self).__init__(icon='Lock.png', **kwargs)

