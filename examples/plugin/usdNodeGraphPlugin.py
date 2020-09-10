
from pxr import Tf
import usdNodeGraph.api as usdNodeGraphApi
from pxr.Usdviewq.qt import QtWidgets, QtCore


class TestWidget(QtWidgets.QTextEdit):
    def __init__(self):
        super(TestWidget, self).__init__()

        self.setPlainText('test widget')

        usdNodeGraphApi.GraphState.addCallback('stageAdded', self.setStage)

    def setStage(self, *args, **kwargs):
        stage = kwargs.get('stage')
        self.setPlainText(str(stage))


class TestPluginContainer(usdNodeGraphApi.PluginContainer):
    def registerPlugins(self):
        usdNodeGraphApi.UsdNodeGraph.registerDockWidget(TestWidget, 'testWidget', 'Test Widget')


Tf.Type.Define(TestPluginContainer)

