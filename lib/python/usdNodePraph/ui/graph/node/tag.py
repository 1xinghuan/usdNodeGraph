# -*- coding: utf-8 -*-
# __author__ = 'XingHuan'
# 8/29/2018


import os
from usdNodePraph.module.sqt import *
from usdNodePraph.utils.res import resource

TAG_W = 20
TAG_H = 20


class PixmapTag(QGraphicsPixmapItem):
    def __init__(self, icon=None, **kwargs):
        super(PixmapTag, self).__init__(**kwargs)

        self.setAcceptHoverEvents(True)

        self.w = TAG_W
        self.h = TAG_H
        self.scale_factor = 10
        self.icon = icon
        self.auto_hide = True

        self._setPixmap()

    def _setPixmap(self, color=None):
        self.setPixmap(resource.get_pixmap(
            'icon',
            self.icon,
            color=color,
            scale=QSize(TAG_W * self.scale_factor, TAG_H * self.scale_factor)
        ))
        self.setScale(1.0 / self.scale_factor)

