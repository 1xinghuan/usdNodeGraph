import sys
from usdNodeGraph.module.sqt import *
from usdNodeGraph.ui.nodeGraph import UsdNodeGraph
from usdNodeGraph.ui.app import MainApplication

if __name__ == '__main__':
    usdFile = ''
    if len(sys.argv) > 1:
        usdFile = sys.argv[1]

    app = MainApplication(sys.argv)

    window = UsdNodeGraph()
    window.show()
    window.setUsdFile(usdFile)

    sys.exit(app.exec_())

