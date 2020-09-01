# -*- coding: utf-8 -*-
# __author__ = 'XingHuan'

import json
from pxr import Usd, Sdf, Kind, UsdGeom
from .node import Node
from usdNodeGraph.ui.graph.other.tag import PixmapTag
from usdNodeGraph.core.parameter import (
    Vec3fParameter, TokenArrayParameter)
from usdNodeGraph.utils.const import consts


ATTR_CHECK_OP = consts(
    EXACT='exact',
    START='start',
)


class UsdNode(Node):
    nodeType = 'Usd'
    nodeItemType = 'UsdNodeItem'

    def __init__(
            self,
            stage=None, layer=None,
            name='', primPath=None,
            *args, **kwargs
    ):
        self._stage = stage
        self._layer = layer
        self._name = name
        self._metadata = {}

        self._primPaths = []
        if primPath is not None:
            self._primPaths.append(primPath)

        super(UsdNode, self).__init__(*args, **kwargs)

    def setMetaData(self, key, value):
        self._metadata[key] = value

    def getMetaDataValue(self, key):
        return self._metadata.get(key)

    def getMetaDataKeys(self):
        return self._metadata.keys()

    def getMetaDataAsString(self):
        return json.dumps(self._metadata, indent=4)

    def _syncParameters(self):
        super(UsdNode, self)._syncParameters()
        self.parameter('name').setValueQuietly(self._name)

    def getStage(self):
        return self._stage

    def execute(self, stage, prim):
        if not self.parameter('disable').getValue():
            self._beforeExecute(stage, prim)
            result = self._execute(stage, prim)
            self._afterExecute(*result)
            return result
        else:
            return stage, prim

    def _beforeExecute(self, stage, prim):
        self.clearPrimPath()

    def _afterExecute(self, stage, prim):
        self.addPrimPath(prim.GetPath().pathString)
    
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

    def getPrimPath(self):
        return self._primPaths


class _PrimNode(UsdNode):
    nodeType = 'Prim'

    def __init__(self, primSpec=None, *args, **kwargs):
        self._primSpec = primSpec
        super(_PrimNode, self).__init__(*args, **kwargs)

    def _syncParameters(self):
        super(_PrimNode, self)._syncParameters()
        if self._primSpec is not None:
            self.parameter('primName').setValueQuietly(self._primSpec.name)

            for key in self._primSpec.ListInfoKeys():
                if key in [
                    'variantSetNames',
                    'variantSelection',
                    'references',
                ]:
                    continue
                # param = self.addParameter(key, )  # metadata value type?
                param = self.parameter(key)
                value = self._primSpec.GetInfo(key)
                if param is not None:
                    param.setValueQuietly(value)
                else:
                    self.setMetaData(key, value)

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

    def _execute(self, stage, prim):
        primPath = self._getCurrentExecutePrimPath(prim)
        newPrim = stage.OverridePrim(primPath)

        parameters = self._parameters.values()
        params = [
            param for param in parameters if not param.isBuiltIn() and (param.isOverride() or param.hasMetaData())
        ]
        for param in params:
            paramName = param.name()
            if paramName not in ['primName']:
                newPrim.SetMetadata(paramName, param.getValue())

        for key in self.getMetaDataKeys():
            newPrim.SetMetadata(key, self.getMetaDataValue(key))

        return stage, newPrim


class LayerNode(UsdNode):
    nodeType = 'Layer'
    fillNormalColor = (50, 60, 70, 150)
    borderNormalColor = (250, 250, 250, 150)

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
    fillNormalColor = (50, 60, 70)
    borderNormalColor = (250, 250, 250, 200)

    def __init__(self, *args, **kwargs):
        super(RootNode, self).__init__(*args, **kwargs)

    def _syncParameters(self):
        super(RootNode, self)._syncParameters()
        if self._layer is not None:
            rootPrim = self._layer.GetPrimAtPath('/')
            for key in rootPrim.ListInfoKeys():
                if key in [
                    'subLayers',
                    'subLayerOffsets',
                ]:
                    continue
                # param = self.addParameter(key, )  # metadata value type?
                param = self.parameter(key)
                value = rootPrim.GetInfo(key)
                if param is not None:
                    param.setValueQuietly(value)
                else:
                    self.setMetaData(key, value)

    def _initParameters(self):
        super(RootNode, self)._initParameters()
        self.addParameter('defaultPrim', 'string', defaultValue='', order=3)
        self.addParameter('upAxis', 'choose', defaultValue='', order=2)
        self.addParameter('startTimeCode', 'float', defaultValue=0, label='Start', order=0)
        self.addParameter('endTimeCode', 'float', defaultValue=0, label='End', order=1)

        self.parameter('upAxis').addItems(['X', 'Y', 'Z'])

    def _execute(self, stage, prim):
        rootPrim = stage.GetPrimAtPath('/')
        # rootLayer = stage.GetRootLayer()

        parameters = self._parameters.values()
        params = [
            param for param in parameters if not param.isBuiltIn() and (param.isOverride() or param.hasMetaData())
        ]
        for param in params:
            paramName = param.name()
            rootPrim.SetMetadata(paramName, param.getValue())

        for key in self.getMetaDataKeys():
            rootPrim.SetMetadata(key, self.getMetaDataValue(key))

        return stage, rootPrim


class PrimDefineNode(_PrimNode):
    nodeType = 'PrimDefine'
    fillNormalColor = (50, 60, 70)
    borderNormalColor = (200, 250, 200, 200)


class PrimOverrideNode(_PrimNode):
    nodeType = 'PrimOverride'
    fillNormalColor = (50, 60, 70)
    borderNormalColor = (200, 200, 250, 200)


class _RefNode(UsdNode):
    nodeType = '_Ref'
    fillNormalColor = (50, 60, 70)
    borderNormalColor = (200, 150, 150, 200)

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
    fillNormalColor = (50, 70, 60)
    borderNormalColor = (250, 250, 250, 200)
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
            return False
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
        for attrName in attrs:
            if cls._checkIsAttrNeeded(attrName):
                return True
        return False

    def __init__(self, primSpec=None, *args, **kwargs):
        self._primSpec = primSpec
        super(AttributeSetNode, self).__init__(*args, **kwargs)

    def _syncParameters(self):
        super(AttributeSetNode, self)._syncParameters()
        if self._primSpec is not None:
            for name, attribute in self._primSpec.attributes.items():
                self._addAttributeParameter(attribute)

    def _generateParamLabel(self, name):
        return name

    def _addAttributeParameter(self, attribute):
        attributeName = attribute.name
        attributeType = str(attribute.typeName)
        # attributeType = attribute.valueType.pythonClass
        # print attributeName, attributeType
        # print attribute.valueType
        needed = self._checkIsAttrNeeded(attributeName)
        if not needed:
            return

        param = self.addParameter(
            attributeName, attributeType,
            custom=True, label=self._generateParamLabel(attributeName)
        )
        if param is not None:
            for key in attribute.ListInfoKeys():
                if key not in [
                    'typeName',
                    'default',
                    'timeSamples',
                    'connectionPaths',
                ]:
                    param.setMetaData(key, attribute.GetInfo(key))

            if attribute.HasInfo('connectionPaths'):
                connectionPathList = attribute.connectionPathList.GetAddedOrExplicitItems()
                connect = connectionPathList[0]
                param.setConnectQuietly(connect.pathString)
            if attribute.HasInfo('timeSamples'):
                param.setTimeSamplesQuietly(attribute.GetInfo('timeSamples'))
            else:
                # print attribute.default, type(attribute.default)
                value = attribute.default
                param.setValueQuietly(value)

    def _initParameters(self):
        super(AttributeSetNode, self)._initParameters()
        pass

    def _whenParamterValueChanged(self, parameter):
        super(AttributeSetNode, self)._whenParamterValueChanged(parameter)
        if not parameter.isBuiltIn():
            attrName = parameter.name()
            for primPath in self._primPaths:
                prim = self._stage.GetPrimAtPath(primPath)
                if not prim.IsValid():
                    continue
                self._setPrimAttributeFromParameter(prim, parameter)

    def _setPrimAttributeFromParameter(self, prim, parameter):
        attrName = parameter.name()
        if not prim.HasAttribute(attrName):
            attribute = prim.CreateAttribute(attrName, parameter.valueTypeName)
        else:
            attribute = prim.GetAttribute(attrName)

        for key in parameter.getMetaDataKyes():
            attribute.SetMetadata(key, parameter.getMetaDataValue(key))

        if parameter.hasConnect():
            attribute.SetConnections([parameter.getConnect()])
        elif parameter.hasKey():
            for time, value in parameter.getTimeSamples().items():
                attribute.Set(value, time)
        else:
            attribute.Set(parameter.getValue())

    def _execute(self, stage, prim):
        parameters = self._parameters.values()
        params = [
            param for param in parameters if not param.isBuiltIn() and (param.isOverride() or param.hasMetaData())
        ]
        for param in params:
            # print(param.name(), param.getValue(), param.hasKey())
            self._setPrimAttributeFromParameter(prim, param)
        return stage, prim


class TransformNode(AttributeSetNode):
    nodeType = 'Transform'
    fillNormalColor = (60, 80, 70)
    borderNormalColor = (250, 250, 250, 200)
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

    def _generateParamLabel(self, name):
        return name.replace('xformOp:', '')

    def _syncParameters(self):
        super(TransformNode, self)._syncParameters()
        for primPath in self._primPaths:
            prim = self._stage.GetPrimAtPath(primPath)
            # for attr in prim.GetAttributes():
            #     print attr, type(attr)


class RelationshipSetNode(UsdNode):
    nodeType = 'RelationshipSet'
    fillNormalColor = (70, 60, 50)
    borderNormalColor = (250, 250, 250, 200)

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
    fillNormalColor = (50, 60, 70)
    borderNormalColor = (200, 200, 150)


class VariantSetNode(_VariantNode):
    nodeType = 'VariantSet'

    def __init__(self, variantSet=None, variantSetName=None, variantList=None, *args, **kwargs):
        super(VariantSetNode, self).__init__(*args, **kwargs)

        self.item.addTag(PixmapTag('VariantSet.png'), position=0.25)

        if variantSetName is not None:
            self.parameter('variantSetName').setValueQuietly(variantSetName)
        if variantList is not None:
            self.parameter('variantList').setValueQuietly(variantList)

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

    def __init__(self, variantSetName='', variantSelected='', options=None, *args, **kwargs):
        super(VariantSelectNode, self).__init__(*args, **kwargs)

        self.item.addTag(PixmapTag('VariantSelect.png'), position=0.25)

        self.parameter('variantSetName').setValueQuietly(variantSetName)
        self.parameter('variantSelected').setValueQuietly(variantSelected)
        if options is not None:
            self.parameter('variantSelected').addItems(options)

    def _initParameters(self):
        super(VariantSelectNode, self)._initParameters()
        self.addParameter('variantSetName', 'string', defaultValue='')
        self.addParameter('variantSelected', 'choose', defaultValue='')

    def _whenParamterValueChanged(self, parameter):
        super(VariantSelectNode, self)._whenParamterValueChanged(parameter)
        if parameter.name() == 'variantSelected':
            variantSetName = self.parameter('variantSetName').getValue()
            for primPath in self._primPaths:
                prim = self._stage.GetPrimAtPath(primPath)
                if not prim.IsValid():
                    continue
                variantSet = prim.GetVariantSet(variantSetName)
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
        # variantSetName = self.parameter('variantSetName').getValue()
        # variantSelected = self.parameter('variantSelected').getValue()
        #
        # variantSet = prim.GetVariantSet(variantSetName)
        # variantSet.SetVariantSelection(variantSelected)

        return stage, prim

    def getVariantSet(self, prim):
        variantSetName = self.parameter('variantSetName').getValue()
        variantSet = prim.GetVariantSet(variantSetName)
        return variantSet

    def getVariantSelection(self):
        return self.parameter('variantSelected').getValue()


class MaterialAssignNode(UsdNode):
    nodeType = 'MaterialAssign'
    fillNormalColor = (50, 60, 80)
    borderNormalColor = (250, 250, 250, 200)

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


Node.registerNode(LayerNode)
Node.registerNode(RootNode)
Node.registerNode(PrimDefineNode)
Node.registerNode(PrimOverrideNode)
Node.registerNode(ReferenceNode)
Node.registerNode(PayloadNode)

Node.registerNode(AttributeSetNode)
Node.registerNode(TransformNode)
Node.registerNode(RelationshipSetNode)

Node.registerNode(VariantSetNode)
Node.registerNode(VariantSelectNode)
Node.registerNode(VariantSwitchNode)

Node.registerNode(MaterialAssignNode)


Node.setParamDefault(LayerNode.nodeType, 'label', '[python os.path.basename("[value layerPath]")]')
Node.setParamDefault(RootNode.nodeType, 'label', '/')
Node.setParamDefault(PrimDefineNode.nodeType, 'label', '/[value primName]')
Node.setParamDefault(PrimOverrideNode.nodeType, 'label', '/[value primName]')
Node.setParamDefault(ReferenceNode.nodeType, 'label', '[python os.path.basename("[value assetPath]")]')
Node.setParamDefault(PayloadNode.nodeType, 'label', '[python os.path.basename("[value assetPath]")]')

Node.setParamDefault(MaterialAssignNode.nodeType, 'label', '[python os.path.basename("[value material]")]')

Node.setParamDefault(VariantSetNode.nodeType, 'label', '{[value variantSetName]:[value variantList]}')
Node.setParamDefault(VariantSelectNode.nodeType, 'label', '{[value variantSetName]=[value variantSelected]}')
Node.setParamDefault(VariantSwitchNode.nodeType, 'label', '{[value variantSetName]?=[value variantSelected]}')


