

usdview plugin:
export PYTHONPATH=$USD_NODEGRAPH_ROOT/lib/python:$PYTHONPATH
export PXR_PLUGINPATH_NAME=$USD_NODEGRAPH_ROOT/plugin:$PXR_PLUGINPATH_NAME


maya:
export PYTHONPATH=$USD_NODEGRAPH_ROOT/lib/python:$PYTHONPATH

from AL import usdmaya
stageCache = usdmaya.StageCache.Get()
stages = stageCache.GetAllStages()
stage = stages[0]

import usdNodeGraph.ui.nodeGraph as usdNodeGraph
reload(usdNodeGraph)
usdNodeGraph.UsdNodeGraph.registerActionShortCut('open_file', None)
usdNodeGraph.UsdNodeGraph.registerActionShortCut('reload_layer', 'Ctrl+R')

nodeGraph = usdNodeGraph.UsdNodeGraph()

nodeGraph.show()
nodeGraph.setStage(stage)


