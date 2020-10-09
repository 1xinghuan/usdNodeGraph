
from pxr import Tf
from pxr.Usdviewq.plugin import PluginContainer
from pxr.Usdviewq.qt import QtWidgets, QtCore


def whenStateTimeChanged(**kwargs):
    # todo: can't set frame from usdviewApi
    pass


def openNodeGraph(usdviewApi):
    from usdNodeGraph.api import GraphState, Node, UsdNodeGraph

    def test_func():
        print('Support Node Types:')
        print(Node.getAllNodeClassNames())

    GraphState.addCallback('stageTimeChanged', whenStateTimeChanged)

    UsdNodeGraph.registerActions([
        ['Test Menu', [
            ['test_action', 'Test Action', None, test_func]
        ]],
    ])

    UsdNodeGraph.registerActionShortCut('open_file', None)
    # UsdNodeGraph.registerActionShortCut('reload_layer', None)

    mainWindow = usdviewApi.qMainWindow

    if not hasattr(mainWindow, 'nodeGraph'):
        nodeGraph = UsdNodeGraph(app='usdview')
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
        mainWindow.addDockWidget(QtCore.Qt.RightDockWidgetArea, mainWindow.nodeGraphDock)

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
        nodeGraphMenu = plugUIBuilder.findOrCreateMenu('NodeGraph')
        nodeGraphMenu.addItem(self.openItem)


Tf.Type.Define(NodeGraphPluginContainer)

