# -*- coding: utf-8 -*-
# __author__ = 'XingHuan'


from pxr import Usd, Sdf, Kind, UsdGeom, UsdShade
from usdNodeGraph.module.sqt import *
from .node import Node, registerNode, setParamDefault
from .nodeItem import NodeItem
from .tag import PixmapTag
from usdNodeGraph.ui.parameter.parameter import (
    Parameter, StringParameter, Vec3fParameter, TokenArrayParameter)
from usdNodeGraph.utils.const import consts


ATTR_CHECK_OP = consts(
    EXACT = 'exact',
    START = 'start',
)


class UsdNodeItem(NodeItem):
    def execute(self, stage, prim):
        return self.nodeObject.execute(stage, prim)


class UsdNode(Node):
    nodeType = 'Usd'
    nodeItem = UsdNodeItem

    def __init__(self, stage=None, layer=None, name='', primPath=None, *args, **kwargs):
        self._stage = stage
        self._layer = layer
        self._name = name
        self._primPaths=[]
        if primPath is not None:
            self._primPaths.append(primPath)

        super(UsdNode, self).__init__(*args, **kwargs)

    def _syncParameters(self):
        super(UsdNode, self)._syncParameters()
        self.parameter('name').setValueQuietly(self._name)

    def getStage(self):
        return self._stage

    def execute(self, stage, prim):
        if not self.parameter('disable').getValue():
            return self._execute(stage, prim)
        else:
            return stage, prim
    
    def _execute(self, stage, prim):
        return stage, prim

    def applyChanges(self):
        if self._stage is not None:
            for primPath in self._primPaths:
                prim = self._stage.GetPrimAtPath(primPath)
                self.execute(self._stage, prim)

    def addPrimPath(self, primPath):
        if primPath is not None:
            self._primPaths.append(primPath)

    def removePrimPath(self, primPath):
        if primPath in self._primPaths:
            self._primPaths.remove(primPath)

    def clearPrimPath(self):
        self._primPaths = []


class _PrimNode(UsdNode):
    nodeType = 'Prim'

    def __init__(self, primSpec=None, *args, **kwargs):
        self._primSpec = primSpec
        super(_PrimNode, self).__init__(*args, **kwargs)

    def _syncParameters(self):
        super(_PrimNode, self)._syncParameters()
        if self._primSpec is not None:
            self.parameter('primName').setValueQuietly(self._primSpec.name)
            if self._primSpec.typeName:
                self.parameter('typeName').setValueQuietly(self._primSpec.typeName)
            if self._primSpec.kind:
                self.parameter('kind').setValueQuietly(self._primSpec.kind)

    def _initParameters(self):
        super(_PrimNode, self)._initParameters()
        self.addParameter('primName', 'string', defaultValue='')
        self.addParameter('typeName', 'string', defaultValue='')
        self.addParameter('kind', 'string', defaultValue='')

    def _getCurrentExecutePrimPath(self, prim):
        primPath = prim.GetPath().pathString
        if primPath == '/':
            primPath = ''
        primName = self.parameter('primName').getValue()
        primPath = '{}/{}'.format(primPath, primName)
        return primPath


class LayerNode(UsdNode):
    nodeType = 'Layer'
    fillNormalColor = QtGui.QColor(50, 60, 70, 150)
    borderNormalColor = QtGui.QColor(250, 250, 250, 150)

    def __init__(self, layerPath='', layerOffset=None, *args, **kwargs):
        self._layerPath = layerPath
        self._layerOffset = layerOffset
        super(LayerNode, self).__init__(*args, **kwargs)

    def _syncParameters(self):
        super(LayerNode, self)._syncParameters()
        self.parameter('layerPath').setValueQuietly(self._layerPath)
        # self.parameter('layerOffset').setValueQuietly(self._layerOffset.offset)
        # self.parameter('layerScale').setValueQuietly(self._layerOffset.scale)

    def _initParameters(self):
        super(LayerNode, self)._initParameters()
        self.addParameter('layerPath', 'string', defaultValue='')
        # self.addParameter('layerOffset', 'float', defaultValue=0.0)
        # self.addParameter('layerScale', 'float', defaultValue=1.0)

    def _execute(self, stage, prim):
        layerPath = self.parameter('layerPath').getValue()
        # layerOffset = self.parameter('layerOffset').getValue()
        # layerScale = self.parameter('layerScale').getValue()
        #
        # layerOffset = Sdf.LayerOffset(offset=layerOffset, scale=layerScale)

        stage.GetRootLayer().subLayerPaths.append(layerPath)

        return stage, prim


class RootNode(UsdNode):
    nodeType = 'Root'
    fillNormalColor = QtGui.QColor(50, 60, 70)
    borderNormalColor = QtGui.QColor(250, 250, 250, 200)

    def __init__(self, *args, **kwargs):
        super(RootNode, self).__init__(*args, **kwargs)

    def _syncParameters(self):
        super(RootNode, self)._syncParameters()
        if self._layer is not None:
            if self._layer.defaultPrim != '':
                self.parameter('defaultPrim').setValueQuietly(self._layer.defaultPrim)
            if self._layer.HasStartTimeCode():
                self.parameter('startTimeCode').setValueQuietly(self._layer.startTimeCode)
            if self._layer.HasEndTimeCode():
                self.parameter('endTimeCode').setValueQuietly(self._layer.endTimeCode)

        # todo: how to get layer's upAxis, not stage?
        if self._stage is not None:
            upAxis = UsdGeom.GetStageUpAxis(self._stage)
            self.parameter('upAxis').setValueQuietly(upAxis)

    def _initParameters(self):
        super(RootNode, self)._initParameters()
        self.addParameter('defaultPrim', 'string', defaultValue='', order=3)
        self.addParameter('upAxis', 'choose', defaultValue='', order=2)
        self.addParameter('startTimeCode', 'float', defaultValue=0, label='Start', order=0)
        self.addParameter('endTimeCode', 'float', defaultValue=0, label='End', order=1)

        self.parameter('upAxis').addItems(['X', 'Y', 'Z'])

    def _execute(self, stage, prim):
        newPrim = stage.GetPrimAtPath('/')
        rootLayer = stage.GetRootLayer()

        startTimeCode = self.parameter('startTimeCode').getValue()
        endTimeCode = self.parameter('endTimeCode').getValue()
        defaultPrim = self.parameter('defaultPrim').getValue()
        upAxis = self.parameter('upAxis').getValue()

        if startTimeCode is not None and startTimeCode != '':
            rootLayer.startTimeCode = startTimeCode
        if endTimeCode is not None and endTimeCode != '':
            rootLayer.endTimeCode = endTimeCode
        if defaultPrim != '':
            rootLayer.defaultPrim = defaultPrim
        if upAxis != '':
            UsdGeom.SetStageUpAxis(stage, getattr(UsdGeom.Tokens, upAxis.lower()))

        return stage, newPrim


class PrimDefineNode(_PrimNode):
    nodeType = 'PrimDefine'
    fillNormalColor = QtGui.QColor(50, 60, 70)
    borderNormalColor = QtGui.QColor(200, 250, 200, 200)

    def __init__(self, *args, **kwargs):
        super(PrimDefineNode, self).__init__(*args, **kwargs)

    def _execute(self, stage, prim):
        primPath = self._getCurrentExecutePrimPath(prim)
        typeName = self.parameter('typeName').getValue()
        kindStr = self.parameter('kind').getValue()

        newPrim = stage.OverridePrim(primPath)
        newPrim.SetSpecifier(Sdf.SpecifierDef)
        newPrim.SetTypeName(typeName)

        if kindStr != '':
            modelAPI = Usd.ModelAPI(newPrim)
            modelAPI.SetKind(getattr(Kind.Tokens, kindStr))

        return stage, newPrim


class PrimOverrideNode(_PrimNode):
    nodeType = 'PrimOverride'
    fillNormalColor = QtGui.QColor(50, 60, 70)
    borderNormalColor = QtGui.QColor(200, 200, 250, 200)

    def __init__(self, *args, **kwargs):
        super(PrimOverrideNode, self).__init__(*args, **kwargs)

    def _execute(self, stage, prim):
        primPath = self._getCurrentExecutePrimPath(prim)
        typeName = self.parameter('typeName').getValue()
        kindStr = self.parameter('kind').getValue()

        newPrim = stage.OverridePrim(primPath)
        # newPrim.SetSpecifier(Sdf.SpecifierDef)
        newPrim.SetTypeName(typeName)

        if kindStr != '':
            modelAPI = Usd.ModelAPI(newPrim)
            modelAPI.SetKind(getattr(Kind.Tokens, kindStr))

        return stage, newPrim


class _RefNode(UsdNode):
    nodeType = '_Ref'
    fillNormalColor = QtGui.QColor(50, 60, 70)
    borderNormalColor = QtGui.QColor(200, 150, 150, 200)

    def _initParameters(self):
        super(_RefNode, self)._initParameters()
        self.addParameter('assetPath', 'string', defaultValue='')
        self.addParameter('layerOffset', 'float', defaultValue=0.0)
        self.addParameter('layerScale', 'float', defaultValue=1.0)

    def _getLayerOffset(self):
        layerOffset = self.parameter('layerOffset').getValue()
        layerScale = self.parameter('layerScale').getValue()

        layerOffset = Sdf.LayerOffset(offset=layerOffset, scale=layerScale)

        return layerOffset


class ReferenceNode(_RefNode):
    nodeType = 'Reference'

    def __init__(self, reference=None, *args, **kwargs):
        super(ReferenceNode, self).__init__(*args, **kwargs)

        self.item.addTag(PixmapTag('Reference.png'), position=0.25)

        if reference is not None:
            self.parameter('assetPath').setValueQuietly(reference.assetPath)
            if reference.layerOffset.offset != 0:
                self.parameter('layerOffset').setValueQuietly(reference.layerOffset.offset)
            if reference.layerOffset.scale != 1:
                self.parameter('layerScale').setValueQuietly(reference.layerOffset.scale)

    def _execute(self, stage, prim):
        assetPath = self.parameter('assetPath').getValue()

        prim.GetReferences().SetReferences([
            Sdf.Reference(assetPath, layerOffset=self._getLayerOffset())
        ])

        return stage, prim


class PayloadNode(_RefNode):
    nodeType = 'Payload'

    def __init__(self, payload=None, *args, **kwargs):
        super(PayloadNode, self).__init__(*args, **kwargs)

        self.item.addTag(PixmapTag('Payload.png'), position=0.25)

        if payload is not None:
            self.parameter('assetPath').setValueQuietly(payload.assetPath)
            if payload.primPath.pathString != '':
                self.parameter('primPath').setValueQuietly(payload.primPath.pathString)
            if payload.layerOffset.offset != 0:
                self.parameter('layerOffset').setValueQuietly(payload.layerOffset.offset)
            if payload.layerOffset.scale != 1:
                self.parameter('layerScale').setValueQuietly(payload.layerOffset.scale)

    def _initParameters(self):
        super(PayloadNode, self)._initParameters()
        self.addParameter('primPath', 'string', defaultValue='')

    def _execute(self, stage, prim):
        assetPath = self.parameter('assetPath').getValue()
        primPath = self.parameter('primPath').getValue()

        payload = Sdf.Payload(assetPath, primPath, self._getLayerOffset())
        prim.SetPayload(payload)

        return stage, prim


class AttributeSetNode(UsdNode):
    nodeType = 'AttributeSet'
    fillNormalColor = QtGui.QColor(50, 70, 60)
    borderNormalColor = QtGui.QColor(250, 250, 250, 200)
    onlyAttrList = []
    ignoreAttrList = [
        [ATTR_CHECK_OP.START, 'xformOp'],
    ]

    @classmethod
    def _checkIsAttrNeeded(cls, attrName):
        if len(cls.onlyAttrList) != 0:
            for i in cls.onlyAttrList:
                if i[0] == 'exact':
                    if i[1] == attrName:
                        return True
                elif i[0] == 'start':
                    if attrName.startswith(i[1]):
                        return True
        for i in cls.ignoreAttrList:
            if i[0] == 'exact':
                if i[1] == attrName:
                    return False
            elif i[0] == 'start':
                if attrName.startswith(i[1]):
                    return False
        return True

    @classmethod
    def _checkIsNodeNeeded(cls, attrs):
        result = False
        for attrName in attrs:
            if cls._checkIsAttrNeeded(attrName):
                return True

    def __init__(self, primSpec=None, *args, **kwargs):
        self._primSpec = primSpec
        super(AttributeSetNode, self).__init__(*args, **kwargs)

    def _syncParameters(self):
        super(AttributeSetNode, self)._syncParameters()
        if self._primSpec is not None:
            for name, attribute in self._primSpec.attributes.items():
                self._addAttributeParameter(attribute)

    def _addAttributeParameter(self, attribute):
        attributeName = attribute.name
        attributeType = str(attribute.typeName)
        # attributeType = attribute.valueType.pythonClass
        # print attributeName,attributeType
        # print attribute.valueType
        needed = self._checkIsAttrNeeded(attributeName)
        if not needed:
            return

        param = self.addParameter(attributeName, attributeType, custom=True)
        if param is not None:
            if attribute.HasInfo('connectionPaths'):
                connectionPathList = attribute.connectionPathList.GetAddedOrExplicitItems()
                connect = connectionPathList[0]
                param.setConnectQuietly(connect.pathString)
            if attribute.HasInfo('timeSamples'):
                param.setTimeSamplesQuietly(attribute.GetInfo('timeSamples'))
            else:
                # print attribute.default, type(attribute.default)
                param.setValueQuietly(attribute.default)

    def _initParameters(self):
        super(AttributeSetNode, self)._initParameters()
        pass

    def _whenParamterValueChanged(self, parameter):
        super(AttributeSetNode, self)._whenParamterValueChanged(parameter)
        if not parameter.isBuiltIn():
            attrName = parameter.name()
            for primPath in self._primPaths:
                prim = self._stage.GetPrimAtPath(primPath)
                self._setPrimAttributeFromParameter(prim, parameter)

    def _setPrimAttributeFromParameter(self, prim, parameter):
        attrName = parameter.name()
        if not prim.HasAttribute(attrName):
            attribute = prim.CreateAttribute(attrName, parameter.valueTypeName)
            attribute.SetCustom(False)
        else:
            attribute = prim.GetAttribute(attrName)

        if parameter.hasConnect():
            attribute.SetConnections([parameter.getConnect()])
        elif parameter.hasKey():
            for time, value in parameter.getTimeSamples().items():
                attribute.Set(value, time)
        else:
            if parameter.getValue() is not None:
                attribute.Set(parameter.getValue())

    def _execute(self, stage, prim):
        params = [param for param in self._parameters.values() if not param.isBuiltIn() and param.isOverride()]
        for param in params:
            # print(param.name(), param.getValue(), param.hasKey())
            self._setPrimAttributeFromParameter(prim, param)
        return stage, prim


class TransformNode(AttributeSetNode):
    nodeType = 'Transform'
    fillNormalColor = QtGui.QColor(60, 80, 70)
    borderNormalColor = QtGui.QColor(250, 250, 250, 200)
    onlyAttrList = [
        [ATTR_CHECK_OP.START, 'xformOp']
    ]
    ignoreAttrList = []

    def __init__(self, *args, **kwargs):
        super(TransformNode, self).__init__(*args, **kwargs)

    def _initParameters(self):
        super(TransformNode, self)._initParameters()
        self.addParameter(
            'xformOp:translate', 'float3',
            defaultValue=Vec3fParameter.convertValueFromPy([0, 0, 0]),
            label='Translate'
        )
        self.addParameter(
            'xformOp:rotateXYZ', 'float3',
            defaultValue=Vec3fParameter.convertValueFromPy([0, 0, 0]),
            label='Rotate'
        )
        self.addParameter(
            'xformOp:scale', 'float3',
            defaultValue=Vec3fParameter.convertValueFromPy([1, 1, 1]),
            label='Scale'
        )
        self.addParameter(
            'xformOpOrder', 'token[]',
            defaultValue=TokenArrayParameter.convertValueFromPy([
                'xformOp:translate', 'xformOp:rotateXYZ', 'xformOp:scale'
            ]),label='Order'
        )

    def _syncParameters(self):
        super(TransformNode, self)._syncParameters()
        for primPath in self._primPaths:
            prim = self._stage.GetPrimAtPath(primPath)
            for attr in prim.GetAttributes():
                print attr, type(attr)


class RelationshipSetNode(UsdNode):
    nodeType = 'RelationshipSet'
    fillNormalColor = QtGui.QColor(70, 60, 50)
    borderNormalColor = QtGui.QColor(250, 250, 250, 200)

    def __init__(self, primSpec=None, *args, **kwargs):
        super(RelationshipSetNode, self).__init__(*args, **kwargs)

        if primSpec is not None:
            for key, relationship in primSpec.relationships.items():
                if key not in ['material:binding']:
                    self._addRelationshipParameter(relationship)

    def _addRelationshipParameter(self, relationship):
        relationshipName = relationship.name
        targetPathList = [i.pathString for i in relationship.targetPathList.GetAddedOrExplicitItems()]

        param = self.addParameter(relationshipName, 'string[]', custom=True)
        if param is not None:
            param.setValueQuietly(targetPathList)

    def _initParameters(self):
        super(RelationshipSetNode, self)._initParameters()
        pass

    def _execute(self, stage, prim):
        params = [param for param in self._parameters.values() if not param.isBuiltIn()]
        for param in params:
            # print(param.name(), param.getValue(), param.hasKey())
            relationshipName = param.name()
            if not prim.HasRelationship(relationshipName):
                relationship = prim.CreateRelationship(relationshipName)
                relationship.SetCustom(False)
            else:
                relationship = prim.GetRelationship(relationshipName)

            relationship.SetTargets(param.getValue())
        return stage, prim


class _VariantNode(UsdNode):
    nodeType = '_Variant'
    fillNormalColor = QtGui.QColor(50, 60, 70)
    borderNormalColor = QtGui.QColor(200, 200, 150)


class VariantSetNode(_VariantNode):
    nodeType = 'VariantSet'

    def __init__(self, variantSet=None, *args, **kwargs):
        super(VariantSetNode, self).__init__(*args, **kwargs)

        self.item.addTag(PixmapTag('VariantSet.png'), position=0.25)

        if variantSet is not None:
            self.parameter('variantSetName').setValueQuietly(variantSet.name)
            self.parameter('variantList').setValueQuietly([v.name for v in variantSet.variantList])

    def _initParameters(self):
        super(VariantSetNode, self)._initParameters()
        self.addParameter('variantSetName', 'string', defaultValue='')
        self.addParameter('variantList', 'string[]', defaultValue=[])

    def _execute(self, stage, prim):
        variantSetName = self.parameter('variantSetName').getValue()
        variantList = self.parameter('variantList').getValue()

        variantSet = prim.GetVariantSets().AddVariantSet(variantSetName)
        for variant in variantList:
            variantSet.AddVariant(variant)

        return stage, prim


class VariantSelectNode(_VariantNode):
    nodeType = 'VariantSelect'

    def __init__(self, variantSetName='', variantSelected='', primSpec=None, *args, **kwargs):
        super(VariantSelectNode, self).__init__(*args, **kwargs)

        self._primSpec = primSpec

        self.item.addTag(PixmapTag('VariantSelect.png'), position=0.25)

        self.parameter('variantSetName').setValueQuietly(variantSetName)
        self.parameter('variantSelected').setValueQuietly(variantSelected)

        if self._primSpec is not None:
            stagePrim = self._getUsdPrim()
            variantSet = stagePrim.GetVariantSet(variantSetName)
            # variantNameList = [v.name for v in self._primSpec.variantSets.get(variantSetName).variantList]
            variantNameList = variantSet.GetVariantNames()
            self.parameter('variantSelected').addItems(variantNameList)

    def _initParameters(self):
        super(VariantSelectNode, self)._initParameters()
        self.addParameter('variantSetName', 'string', defaultValue='')
        self.addParameter('variantSelected', 'choose', defaultValue='')

    def _getUsdPrim(self):
        primPath = self._primSpec.path
        stagePrim = self._stage.GetPrimAtPath(primPath)
        return stagePrim

    def _paramterValueChanged(self, parameter):
        super(VariantSelectNode, self)._paramterValueChanged(parameter)
        if parameter.name() == 'variantSelected':
            if self._primSpec is not None:
                variantSetName = self.parameter('variantSetName').getValue()

                stagePrim = self._getUsdPrim()
                variantSet = stagePrim.GetVariantSet(variantSetName)
                variantSet.SetVariantSelection(parameter.getValue())

    def _execute(self, stage, prim):
        variantSetName = self.parameter('variantSetName').getValue()
        variantSelected = self.parameter('variantSelected').getValue()

        variantSet = prim.GetVariantSet(variantSetName)
        variantSet.SetVariantSelection(variantSelected)

        return stage, prim


class VariantSwitchNode(_VariantNode):
    nodeType = 'VariantSwitch'

    def __init__(self, variantSetName='', variantSelected='', *args, **kwargs):
        super(VariantSwitchNode, self).__init__(*args, **kwargs)

        self.item.addTag(PixmapTag('VariantSwitch.png'), position=0.25)

        self.parameter('variantSetName').setValueQuietly(variantSetName)
        self.parameter('variantSelected').setValueQuietly(variantSelected)

    def _initParameters(self):
        super(VariantSwitchNode, self)._initParameters()
        self.addParameter('variantSetName', 'string', defaultValue='')
        self.addParameter('variantSelected', 'string', defaultValue='')

    def _execute(self, stage, prim):
        variantSetName = self.parameter('variantSetName').getValue()
        variantSelected = self.parameter('variantSelected').getValue()

        variantSet = prim.GetVariantSet(variantSetName)
        variantSet.SetVariantSelection(variantSelected)

        return stage, prim

    def getVariantSet(self, prim):
        variantSetName = self.parameter('variantSetName').getValue()
        variantSet = prim.GetVariantSet(variantSetName)
        return variantSet


class MaterialAssignNode(UsdNode):
    nodeType = 'MaterialAssign'
    fillNormalColor = QtGui.QColor(50, 60, 80)
    borderNormalColor = QtGui.QColor(250, 250, 250, 200)

    def __init__(self, material=None, *args, **kwargs):
        super(MaterialAssignNode, self).__init__(*args, **kwargs)

        if material is not None:
            self.parameter('material').setValueQuietly(material)

    def _initParameters(self):
        super(MaterialAssignNode, self)._initParameters()
        self.addParameter('material', 'string', defaultValue='')

    def _execute(self, stage, prim):
        materialPath = self.parameter('material').getValue()

        # material prim may not exist
        # materialPrim = stage.GetPrimAtPath(materialPath)
        # material = UsdShade.Material(materialPrim)
        #
        # mesh = UsdGeom.Mesh(prim)
        # UsdShade.MaterialBindingAPI(mesh).Bind(material)

        relationshipName = 'material:binding'

        if not prim.HasRelationship(relationshipName):
            relationship = prim.CreateRelationship(relationshipName)
            relationship.SetCustom(False)
        else:
            relationship = prim.GetRelationship(relationshipName)

        relationship.SetTargets([materialPath])

        return stage, prim


registerNode(LayerNode)
registerNode(RootNode)
registerNode(PrimDefineNode)
registerNode(PrimOverrideNode)
registerNode(ReferenceNode)
registerNode(PayloadNode)

registerNode(AttributeSetNode)
registerNode(TransformNode)
registerNode(RelationshipSetNode)

registerNode(VariantSetNode)
registerNode(VariantSelectNode)
registerNode(VariantSwitchNode)

registerNode(MaterialAssignNode)


setParamDefault(LayerNode.nodeType, 'label', '[python os.path.basename("[value layerPath]")]')
setParamDefault(RootNode.nodeType, 'label', '/')
setParamDefault(PrimDefineNode.nodeType, 'label', '/[value primName]')
setParamDefault(PrimOverrideNode.nodeType, 'label', '/[value primName]')
setParamDefault(ReferenceNode.nodeType, 'label', '[python os.path.basename("[value assetPath]")]')
setParamDefault(PayloadNode.nodeType, 'label', '[python os.path.basename("[value assetPath]")]')

setParamDefault(MaterialAssignNode.nodeType, 'label', '[python os.path.basename("[value material]")]')

setParamDefault(VariantSetNode.nodeType, 'label', '{[value variantSetName]:[value variantList]}')
setParamDefault(VariantSelectNode.nodeType, 'label', '{[value variantSetName]=[value variantSelected]}')
setParamDefault(VariantSwitchNode.nodeType, 'label', '{[value variantSetName]?=[value variantSelected]}')


