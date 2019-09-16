# -*- coding: utf-8 -*-
# __author__ = 'XingHuan'


from pxr import Usd, Sdf, Kind, UsdGeom
from usdNodePraph.module.sqt import *
from .node import NodeItem, registerNode, setNodeDefault
from .node import PixmapTag
from usdNodePraph.ui.parameter.parameter import Parameter, StringParameter


class UsdNodeItem(NodeItem):
    nodeType = 'Usd'

    def __init__(self, stage=None, layer=None, *args, **kwargs):
        super(UsdNodeItem, self).__init__(*args, **kwargs)

        self._stage = stage
        self._layer = layer

    def getStage(self):
        return self._stage

    def execute(self, stage, prim):
        if not self.parameter('disable').getValue():
            return self._execute(stage, prim)
        else:
            return stage, prim
    
    def _execute(self, stage, prim):
        return stage, prim


class _PrimNodeItem(UsdNodeItem):
    nodeType = 'Prim'

    def __init__(self, prim=None, *args, **kwargs):
        super(_PrimNodeItem, self).__init__(*args, **kwargs)

        if prim is not None:
            self.parameter('primName').setValue(prim.name)
            self.parameter('typeName').setValue(prim.typeName)
            self.parameter('kind').setValue(prim.kind)

    def _initParameters(self):
        super(_PrimNodeItem, self)._initParameters()
        self.addParameter('primName', 'string', defaultValue='')
        self.addParameter('typeName', 'string', defaultValue='')
        self.addParameter('kind', 'string', defaultValue='')

    def _get_current_prim_path(self, prim):
        primPath = prim.GetPath().pathString
        if primPath == '/':
            primPath = ''
        primName = self.parameter('primName').getValue()
        primPath = '{}/{}'.format(primPath, primName)
        return primPath


class LayerNodeItem(UsdNodeItem):
    nodeType = 'Layer'
    fillNormalColor = QColor(50, 60, 70, 150)
    borderNormalColor = QColor(250, 250, 250, 150)

    def __init__(self, layerPath='', layerOffset=None, *args, **kwargs):
        super(LayerNodeItem, self).__init__(*args, **kwargs)

        self.parameter('layerPath').setValue(layerPath)
        # todo:
        # self.parameter('layerOffset').setValue(layerOffset)

    def _initParameters(self):
        super(LayerNodeItem, self)._initParameters()
        self.addParameter('layerPath', 'string', defaultValue='')
        self.addParameter('layerOffset', 'string', defaultValue='')

    def _execute(self, stage, prim):
        layerPath = self.parameter('layerPath').getValue()
        # todo:
        # layerOffset = self.parameter('layerOffset').getValue()

        stage.GetRootLayer().subLayerPaths.append(layerPath)

        return stage, prim


class RootNodeItem(UsdNodeItem):
    nodeType = 'Root'
    fillNormalColor = QColor(50, 60, 70)
    borderNormalColor = QColor(250, 250, 250, 200)

    def __init__(self, *args, **kwargs):
        super(RootNodeItem, self).__init__(*args, **kwargs)

        if self._stage is not None:
            rootLayer = self._stage.GetRootLayer()
            upAxis = UsdGeom.GetStageUpAxis(self._stage)

            self.parameter('defaultPrim').setValue(rootLayer.defaultPrim)
            self.parameter('upAxis').setValue(upAxis)

    def _initParameters(self):
        super(RootNodeItem, self)._initParameters()
        self.addParameter('defaultPrim', 'string', defaultValue='')
        self.addParameter('upAxis', 'string', defaultValue='')

    def _execute(self, stage, prim):
        newPrim = stage.GetPrimAtPath('/')
        rootLayer = stage.GetRootLayer()

        defaultPrim = self.parameter('defaultPrim').getValue()
        upAxis = self.parameter('upAxis').getValue()

        if defaultPrim != '':
            rootLayer.defaultPrim = defaultPrim
        if upAxis != '':
            UsdGeom.SetStageUpAxis(stage, getattr(UsdGeom.Tokens, upAxis.lower()))

        return stage, newPrim


class PrimDefineNodeItem(_PrimNodeItem):
    nodeType = 'PrimDefine'
    fillNormalColor = QColor(50, 60, 70)
    borderNormalColor = QColor(200, 250, 200, 200)

    def __init__(self, *args, **kwargs):
        super(PrimDefineNodeItem, self).__init__(*args, **kwargs)

    def _execute(self, stage, prim):
        primPath = self._get_current_prim_path(prim)
        typeName = self.parameter('typeName').getValue()
        kindStr = self.parameter('kind').getValue()

        newPrim = stage.OverridePrim(primPath)
        newPrim.SetSpecifier(Sdf.SpecifierDef)
        newPrim.SetTypeName(typeName)

        if kindStr != '':
            modelAPI = Usd.ModelAPI(newPrim)
            modelAPI.SetKind(getattr(Kind.Tokens, kindStr))

        return stage, newPrim


class PrimOverrideNodeItem(_PrimNodeItem):
    nodeType = 'PrimOverride'
    fillNormalColor = QColor(50, 60, 70)
    borderNormalColor = QColor(200, 200, 250, 200)

    def __init__(self, *args, **kwargs):
        super(PrimOverrideNodeItem, self).__init__(*args, **kwargs)

    def _execute(self, stage, prim):
        primPath = self._get_current_prim_path(prim)
        typeName = self.parameter('typeName').getValue()
        kindStr = self.parameter('kind').getValue()

        newPrim = stage.OverridePrim(primPath)
        # newPrim.SetSpecifier(Sdf.SpecifierDef)
        newPrim.SetTypeName(typeName)

        if kindStr != '':
            modelAPI = Usd.ModelAPI(newPrim)
            modelAPI.SetKind(getattr(Kind.Tokens, kindStr))

        return stage, newPrim


class _RefNodeItem(UsdNodeItem):
    nodeType = '_Ref'
    fillNormalColor = QColor(50, 60, 70)
    borderNormalColor = QColor(200, 150, 150, 200)


class ReferenceNodeItem(_RefNodeItem):
    nodeType = 'Reference'

    def __init__(self, reference=None, *args, **kwargs):
        super(ReferenceNodeItem, self).__init__(*args, **kwargs)

        self.addTag(PixmapTag('Reference.png'), position=0.25)

        if reference is not None:
            self.parameter('assetPath').setValue(reference.assetPath)

    def _initParameters(self):
        super(ReferenceNodeItem, self)._initParameters()
        self.addParameter('assetPath', 'string', defaultValue='')

    def _execute(self, stage, prim):
        assetPath = self.parameter('assetPath').getValue()

        prim.GetReferences().SetReferences([
            Sdf.Reference(assetPath)
        ])

        return stage, prim


class PayloadNodeItem(_RefNodeItem):
    nodeType = 'Payload'

    def __init__(self, payload=None, *args, **kwargs):
        super(PayloadNodeItem, self).__init__(*args, **kwargs)

        self.addTag(PixmapTag('Payload.png'), position=0.25)

        if payload is not None:
            self.parameter('assetPath').setValue(payload.assetPath)
            self.parameter('primPath').setValue(payload.primPath)

    def _initParameters(self):
        super(PayloadNodeItem, self)._initParameters()
        self.addParameter('assetPath', 'string', defaultValue='')
        self.addParameter('primPath', 'string', defaultValue='')

    def _execute(self, stage, prim):
        assetPath = self.parameter('assetPath').getValue()
        primPath = self.parameter('primPath').getValue()

        prim.SetPayload(assetPath, primPath)

        return stage, prim


class AttributeSetNodeItem(UsdNodeItem):
    nodeType = 'AttributeSet'
    fillNormalColor = QColor(50, 70, 60)
    borderNormalColor = QColor(250, 250, 250, 200)

    def __init__(self, prim=None, *args, **kwargs):
        super(AttributeSetNodeItem, self).__init__(*args, **kwargs)

        if prim is not None:
            for name, attribute in prim.attributes.items():
                self._addAttributeParameter(attribute)

    def _addAttributeParameter(self, attribute):
        attributeName = attribute.name
        attributeType = str(attribute.typeName)
        # attributeType = attribute.valueType.pythonClass
        # print attributeName,
        # print attribute.valueType

        param = self.addParameter(attributeName, attributeType)
        if param is not None:
            if attribute.HasInfo('timeSamples'):
                param.setTimeSamples(attribute.GetInfo('timeSamples'))
            else:
                param.setValue(attribute.default)

    def _initParameters(self):
        super(AttributeSetNodeItem, self)._initParameters()
        pass

    def _execute(self, stage, prim):
        params = [param for param in self._parameters.values() if not param.isBuiltIn()]
        for param in params:
            # print(param.name(), param.getValue(), param.hasKey())
            attrName = param.name()
            if not prim.HasAttribute(attrName):
                attribute = prim.CreateAttribute(attrName, param.valueTypeName)
                attribute.SetCustom(False)
            else:
                attribute = prim.GetAttribute(attrName)

            if param.hasKey():
                for time, value in param.getTimeSamples().items():
                    attribute.Set(value, time)
            else:
                if param.getValue() is not None:
                    attribute.Set(param.getValue())
        return stage, prim


class _VariantNodeItem(UsdNodeItem):
    nodeType = '_Variant'
    fillNormalColor = QColor(50, 60, 70)
    borderNormalColor = QColor(200, 200, 150)


class VariantSetNodeItem(_VariantNodeItem):
    nodeType = 'VariantSet'

    def __init__(self, variantSet=None, *args, **kwargs):
        super(VariantSetNodeItem, self).__init__(*args, **kwargs)

        self.addTag(PixmapTag('VariantSet.png'), position=0.25)

        if variantSet is not None:
            self.parameter('variantSetName').setValue(variantSet.name)
            self.parameter('variantList').setValue([v.name for v in variantSet.variantList])

    def _initParameters(self):
        super(VariantSetNodeItem, self)._initParameters()
        self.addParameter('variantSetName', 'string', defaultValue='')
        self.addParameter('variantList', 'string[]', defaultValue=[])


class VariantSelectNodeItem(_VariantNodeItem):
    nodeType = 'VariantSelect'

    def __init__(self, variantSetName='', variantSelected='', prim=None, *args, **kwargs):
        super(VariantSelectNodeItem, self).__init__(*args, **kwargs)

        self._prim = prim

        self.addTag(PixmapTag('VariantSelect.png'), position=0.25)

        self.parameter('variantSetName').setValue(variantSetName)
        self.parameter('variantSelected').setValue(variantSelected)

        if self._prim is not None:
            stagePrim = self._getStagePrim()
            variantSet = stagePrim.GetVariantSet(variantSetName)
            # variantNameList = [v.name for v in self._prim.variantSets.get(variantSetName).variantList]
            variantNameList = variantSet.GetVariantNames()
            self.parameter('variantSelected').addItems(variantNameList)

    def _initParameters(self):
        super(VariantSelectNodeItem, self)._initParameters()
        self.addParameter('variantSetName', 'string', defaultValue='')
        self.addParameter('variantSelected', 'choose', defaultValue='')

    def _getStagePrim(self):
        primPath = self._prim.path
        stagePrim = self._stage.GetPrimAtPath(primPath)
        return stagePrim

    def _paramterValueChanged(self, parameter, value):
        super(VariantSelectNodeItem, self)._paramterValueChanged(parameter, value)
        if parameter.name() == 'variantSelected':
            if self._prim is not None:
                variantSetName = self.parameter('variantSetName').getValue()

                stagePrim = self._getStagePrim()
                variantSet = stagePrim.GetVariantSet(variantSetName)
                variantSet.SetVariantSelection(value)


class VariantSwitchNodeItem(_VariantNodeItem):
    nodeType = 'VariantSwitch'

    def __init__(self, variantSetName='', variantSelected='', *args, **kwargs):
        super(VariantSwitchNodeItem, self).__init__(*args, **kwargs)

        self.addTag(PixmapTag('VariantSwitch.png'), position=0.25)

        self.parameter('variantSetName').setValue(variantSetName)
        self.parameter('variantSelected').setValue(variantSelected)

    def _initParameters(self):
        super(VariantSwitchNodeItem, self)._initParameters()
        self.addParameter('variantSetName', 'string', defaultValue='')
        self.addParameter('variantSelected', 'string', defaultValue='')



class TransformNodeItem(_PrimNodeItem):
    nodeType = 'Transform'

    def __init__(self, *args, **kwargs):
        super(TransformNodeItem, self).__init__(*args, **kwargs)




registerNode(LayerNodeItem)
registerNode(RootNodeItem)
registerNode(PrimDefineNodeItem)
registerNode(PrimOverrideNodeItem)
registerNode(ReferenceNodeItem)
registerNode(PayloadNodeItem)
registerNode(AttributeSetNodeItem)

registerNode(VariantSetNodeItem)
registerNode(VariantSelectNodeItem)
registerNode(VariantSwitchNodeItem)

registerNode(TransformNodeItem)


setNodeDefault(LayerNodeItem.nodeType, 'label', '[python os.path.basename("[value layerPath]")]')
setNodeDefault(RootNodeItem.nodeType, 'label', '/')
setNodeDefault(PrimDefineNodeItem.nodeType, 'label', '/[value primName]')
setNodeDefault(PrimOverrideNodeItem.nodeType, 'label', '/[value primName]')
setNodeDefault(ReferenceNodeItem.nodeType, 'label', '[python os.path.basename("[value assetPath]")]')
setNodeDefault(PayloadNodeItem.nodeType, 'label', '[python os.path.basename("[value assetPath]")]')

setNodeDefault(VariantSetNodeItem.nodeType, 'label', '{[value variantSetName]:[value variantList]}')
setNodeDefault(VariantSelectNodeItem.nodeType, 'label', '{[value variantSetName]=[value variantSelected]}')
setNodeDefault(VariantSwitchNodeItem.nodeType, 'label', '{[value variantSetName]?=[value variantSelected]}')



