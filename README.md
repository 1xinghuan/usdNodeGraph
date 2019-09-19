# UsdNodeGraph

![screenshot01](screenshot/screenshot01.png)

You can use the node view to preview the usd file and simply edit the usd file, such as overriding prim, switching variants, adding references or payloads, and modifying attributes.

Currently, only some types of data are supported, such as:
+ Layer
+ PrimDefine
+ PrimOverride
+ Reference
+ Payload
+ Variant

**If there are some unsupported data in the usd file, they will not be displayed in the view, and the data will be lost when saved.**

## Plugins

usdview:
```bash
export PYTHONPATH=$USD_NODEGRAPH_ROOT/lib/python:$PYTHONPATH
export PYTHONPATH=$USD_NODEGRAPH_ROOT/plugin:$PYTHONPATH
export PXR_PLUGINPATH_NAME=$USD_NODEGRAPH_ROOT/plugin:$PXR_PLUGINPATH_NAME
```

maya:
```bash
export PYTHONPATH=$USD_NODEGRAPH_ROOT/lib/python:$PYTHONPATH
```

```python
from AL import usdmaya
stageCache = usdmaya.StageCache.Get()
stages = stageCache.GetAllStages()
stage = stages[0]
layer = stage.GetEditTarget()

import usdNodeGraph.ui.nodeGraph as usdNodeGraph
reload(usdNodeGraph)
usdNodeGraph.UsdNodeGraph.registerActionShortCut('open_file', None)
usdNodeGraph.UsdNodeGraph.registerActionShortCut('reload_layer', 'Ctrl+R')

nodeGraph = usdNodeGraph.UsdNodeGraph()

nodeGraph.show()
nodeGraph.setStage(stage, layer=layer)
```


