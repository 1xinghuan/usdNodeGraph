# Supports

## Node
+ Create

    Press 'Tab'
    
    ![screenshot01](screenshot/usdnodegraph01.gif)

+ Connect

    ![screenshot01](screenshot/usdnodegraph02.gif)

+ Copy & Paste

    ![screenshot01](screenshot/usdnodegraph03.gif)

+ Disable

    ![screenshot01](screenshot/usdnodegraph04.gif)

+ Shader


## Parameter

+ Edit Number Parameter

    ![screenshot01](screenshot/usdnodegraph06.gif)

+ Add/Remove Keyframe

    ![screenshot01](screenshot/usdnodegraph05.gif)

+ Set/Unset Connect

    todo


+ Add Custom Parameter

    todo


+ Update Stage When Changed(Only for AttributeSet node)

    ![screenshot01](screenshot/usdnodegraph06.gif)
    
+ Override Status Button



## Maya

This is an example workflow using usdNodeGraph. Test with maya 2020.2 and maya-usd 0.3.0.

1. Load the [master.usda](examples/layer/master.usda) file in maya and rename the node to "s00";

2. Open UsdNodeGraph and set the stage(using the code in [README](README.md));

3. Go into set.usda Layer node;

4. Create a PrimDefine node and connect it to 'PrimDefine(/world)'. Set parameter 'primName' to 'house1' and 'typeName' to 'Xform';

5. Create a 'Reference' node and connect it to 'PrimDefine1' node. Set parameter 'assetPath' to the path of [house.usda](examples/model/house.usda);

6. Click **'File->Apply'** or use 'Ctrl+Shift+A' short cut, then you can see the house in maya;

7. Copy the created two nodes and paste, change the 'PrimDefine2' node 'primName' parameter to 'house2'. Apply the changes and there will be two houses in scene. You can check it in maya outliner;

8. Go into layout.usda Layer node;

9. Move the house2 to other place in maya's viewer, go back to UsdNodeGraph and click **'File->Reload Layer'**. There should be two 'PrimOverride' nodes and a 'Transform' node. You can see and edit the translate value in parameter panel after double click the node.

10. You can save current edit by click **'File->Save Layer'**.

