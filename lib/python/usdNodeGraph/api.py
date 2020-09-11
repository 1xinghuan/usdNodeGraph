# -*- coding: utf-8 -*-

from .core.node import Node
from .core.parameter import Parameter
from .core.state import GraphState
from .ui.nodeGraph import UsdNodeGraph
from .ui.plugin import PluginContainer


def setUsdFile(usdFile):
    graph = UsdNodeGraph.getInstance()
    if graph is not None:
        graph.setUsdFile(usdFile)


def addUsdFile(usdFile):
    graph = UsdNodeGraph.getInstance()
    if graph is not None:
        graph.addUsdFile(usdFile)


def addStage(stage, layer=None):
    graph = UsdNodeGraph.getInstance()
    if graph is not None:
        graph.addStage(stage, layer)


def setStage(stage, layer=None):
    graph = UsdNodeGraph.getInstance()
    if graph is not None:
        graph.setStage(stage, layer)


def createNode(nodeType):
    graph = UsdNodeGraph.getInstance()
    if graph is not None:
        return graph.createNode(nodeType)


def findNodeAtPath(path):
    graph = UsdNodeGraph.getInstance()
    if graph is not None:
        return graph.findNodeAtPath(path)

