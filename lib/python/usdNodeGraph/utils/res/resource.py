# -*- coding: utf-8 -*-
# __author__ = 'XingHuan'
# 4/4/2018


import os
import sys
from usdNodeGraph.module.sqt import *

RES_FOLDER = '/'.join(__file__.replace('\\', '/').split('/')[:-3]) + '/resource'


def get_pic(*args):
    path = os.path.join(RES_FOLDER, *args).replace('\\', '/')
    return path


def get_qicon(*args):
    return QIcon(get_pic(*args))


def get_pixmap(*args, **kwargs):
    """
    return QPixmap object based on name and scale
    :param name: pic name
    :param scale: scale factor, list or int
    :return: QPixmap
    """
    path = args[0] if os.path.isfile(args[0]) else get_pic(*args)
    scale = kwargs.get('scale')
    aspect = kwargs.get('aspect', 'keep')
    color = kwargs.get('color')
    error = kwargs.get('error', 'Error01')
    clip = kwargs.get('clip')

    if isinstance(scale, QSize):
        pass
    elif isinstance(scale, (list, tuple)):
        scale = QSize(scale[0], scale[1])
    elif isinstance(scale, int):
        scale = QSize(scale, scale)

    if isinstance(color, QColor):
        pass
    elif color == "auto":
        color = QApplication.instance().palette(None).text().color()
    elif isinstance(color, basestring):
        color = QColor(color)
    elif isinstance(color, int):
        color = QColor(color)
    elif isinstance(color, list):
        color = QColor(color[0], color[1], color[2])
    elif isinstance(color, QWidget):
        widget = color
        is_enabled = widget.isEnabled()
        if not is_enabled:
            widget.setEnabled(True)
        color = widget.palette().text().color()
        if not is_enabled:
            widget.setEnabled(is_enabled)

    img = QImage(path)

    if scale:
        if aspect == 'keep':
            img = img.scaled(scale, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        elif aspect == 'expand':
            img = img.scaled(scale, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        elif aspect == 'width':
            img = img.scaledToWidth(scale.width(), Qt.SmoothTransformation)
        elif aspect == 'height':
            img = img.scaledToHeight(scale.height(), Qt.SmoothTransformation)
    if color:
        img = img.convertToFormat(QImage.Format_Indexed8)
        if img.depth() in [1, 8]:
            for index in range(img.colorCount()):
                src_color = QColor.fromRgba(img.color(index))
                img.setColor(index, QColor(color.red(), color.green(), color.blue(),
                                                 src_color.alpha()).rgba())
        else:
            for row in range(img.height()):
                for col in range(img.width()):
                    src_color = QColor.fromRgba(img.pixel(col, row))
                    if not src_color.alpha():
                        continue
                    img.setPixel(col, row, color.rgb())

    pixmap = QPixmap.fromImage(img)

    if clip and isinstance(clip, (list, tuple)):
        pixmap = pixmap.copy(*clip)

    return pixmap


def get_style(name):
    styleFile = os.path.join(RES_FOLDER, "style", "%s.css" % name)
    styleText = open(styleFile).read()
    styleText = styleText.replace("%s", RES_FOLDER)
    styleText = styleText.replace("\\", "/")
    return styleText


