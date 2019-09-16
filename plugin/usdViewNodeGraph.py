
from pxr import Tf
from pxr.Usdviewq.plugin import PluginContainer
from pxr.Usdviewq.qt import QtWidgets, QtCore


def openNodeGraph(usdviewApi):
    from usdNodePraph.ui.nodeGraph import UsdNodeGraph

    UsdNodeGraph.registerActionShortCut('open_file', None)

    mainWindow = usdviewApi.qMainWindow

    if not hasattr(mainWindow, 'nodeGraph'):
        nodeGraph = UsdNodeGraph()
        nodeGraph.splitDockWidget(
            nodeGraph.parameterPanelDock, nodeGraph.nodeGraphDock,
            QtCore.Qt.Vertical
        )
        nodeGraphDock = QtWidgets.QDockWidget()
        nodeGraphDock.setObjectName('usdNodeGraphDock')
        nodeGraphDock.setWindowTitle('Usd Node Graph')
        nodeGraphDock.setWidget(nodeGraph)

        mainWindow.nodeGraph = nodeGraph
        mainWindow.nodeGraphDock = nodeGraphDock
        mainWindow.addDockwidget(QtCore.Qt.RightDockWidgetArea, mainWindow.nodeGraphDock)

    mainWindow.nodeGraph.show()
    mainWindow.nodeGraph.setStage(usdviewApi.stage)


class NodeGraphPluginContainer(PluginContainer):
    def registerPlugins(self, plugRegistry, usdviewApi):
        self.openItem = plugRegistry.registerCommandPlugin(
            'NodeGraphPluginContainer.Open',
            'Open Node Graph',
            openNodeGraph
        )

    def configureView(self, plugRegistry, plugUIBuilder):
        nodeGraphMenu = plugRegistry.findOrCreateMenu('NodeGraph')
        nodeGraphMenu.addItem(self.openItem)


Tf.Type.Define(NodeGraphPluginContainer)

