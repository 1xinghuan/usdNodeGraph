# -*- coding: utf-8 -*-

import json
import traceback
from pxr import Usd, Sdf, Kind, UsdGeom, Vt
from .node import Node
from usdNodeGraph.ui.graph.other.tag import PixmapTag
from usdNodeGraph.core.parameter import Vec3fParameter, TokenArrayParameter
from usdNodeGraph.utils.const import consts
from usdNodeGraph.core.state.core import GraphState
from usdNodeGraph.ui.utils.log import LogWindow
from usdNodeGraph.utils.pyversion import *

ATTR_CHECK_OP = consts(
    EXACT='exact',
    START='start',
)
LIST_EDITOR_PROXY_EXPLICIT_OP = 'explicit'
LIST_EDITOR_PROXY_ADD_OP = 'added'
LIST_EDITOR_PROXY_APPEND_OP = 'appended'
LIST_EDITOR_PROXY_PREPEND_OP = 'prepended'
LIST_EDITOR_PROXY_OPS = [
    LIST_EDITOR_PROXY_EXPLICIT_OP,
    LIST_EDITOR_PROXY_ADD_OP,
    LIST_EDITOR_PROXY_APPEND_OP,
    LIST_EDITOR_PROXY_PREPEND_OP,
]


class UsdNode(Node):
    nodeType = 'Usd'
    nodeItemType = 'UsdNodeItem'
    nodeGroup = 'Usd'
    _ignoreExecuteParamNames = []

    @classmethod
    def getIgnoreExecuteParamNames(cls):
        _ignoreExecuteParamNames = [
            'name',
            'label',
            'x',
            'y',
            'locked',
            'disable',
            'fillColor',
            'borderColor',
        ]
        _ignoreExecuteParamNames.extend(cls._ignoreExecuteParamNames)
        return _ignoreExecuteParamNames

    def __init__(
            self,
            stage=None, layer=None,
            name='', primPath=None, primSpec=None,
            *args, **kwargs
    ):
        self._stage = stage
        self._layer = layer
        self._primSpec = primSpec
        self._name = name
        self._metadata = {}
        self._defaultMetadata = {}

        self._primPaths = []
        if primPath is not None:
            self._primPaths.append(primPath)

        super(UsdNode, self).__init__(*args, **kwargs)

    def hasMetadatas(self):
        return self._metadata != {}

    def hasMetadata(self, key):
        return key in self._metadata

    def setMetadata(self, key, value):
        self._metadata[key] = str(value)

    def getMetadataValue(self, key, default=None):
        strValue = self._metadata.get(key, default)
        try:
            value = eval(strValue)
        except:
            value = strValue
        return value

    def getMetadataKeys(self):
        return list(self._metadata.keys())

    def getMetadatas(self):
        return self._metadata

    def getDefaultMetadatas(self):
        return self._defaultMetadata

    def getMetadatasAsString(self):
        return json.dumps(self._metadata, indent=4)

    def _syncParameters(self):
        super(UsdNode, self)._syncParameters()
        self.parameter('name').setValueQuietly(self._name)

    def getStage(self):
        return self._stage

    def execute(self, stage, prim):
        if not self.parameter('disable').getValue():
            self._beforeExecute(stage, prim)
            try:
                stage, prim = self._execute(stage, prim)
            except(Exception) as e:
                traceback.print_exc()
                LogWindow.error('Node Execute Error: {}\n{}'.format(self.name(), e))
            self._afterExecute(stage, prim)
            return stage, prim
        else:
            return stage, prim

    def _beforeExecute(self, stage, prim):
        parentPaths = []
        parentNodes = self.item.getSources()
        for n in parentNodes:
            parentPaths.extend(n.nodeObject.getPrimPath())
        self.reSyncPath(parentPaths)

    def _afterExecute(self, stage, prim):
        pass

    def _execute(self, stage, prim):
        return stage, prim

    def applyChanges(self):
        if self._stage is None:
            return
        for primPath in self._primPaths:
            prim = self._stage.GetPrimAtPath(primPath)
            if prim.IsValid():
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

    def getExecuteParams(self):
        parameters = list(self._parameters.values())
        params = [
            param for param in parameters if (
                    (param.isOverride() or param.hasMetadatas())
                    and param.name() not in self.getIgnoreExecuteParamNames()
            )
        ]
        return params

    def _combinePaths(self, parentPath, path):
        if parentPath[-1] == '}' and path[0] == '{':
            last_variant_set_name = parentPath.split('{')[-1].split('=')[0]
            current_variant_set_name = path.split('{')[-1].split('=')[0]
            if last_variant_set_name == current_variant_set_name:
                return '{'.join(parentPath.split('{')[:-1]) + '{' + path[1:]
            else:
                return parentPath + path
        elif parentPath[-1] in ['/', '}'] or path[0] == '{':
            return parentPath + path
        else:
            return parentPath + '/' + path

    def reSyncPath(self, parentPaths=None):
        self.clearPrimPath()

        if self.Class() == 'Root':
            self.addPrimPath('/')
        else:
            if self.NodeTypes().isSubType('Prim'):
                for parentPath in parentPaths:
                    self.addPrimPath(self._combinePaths(parentPath, self.parameter('primName').getValue()))
            elif self.Class() in ['VariantSelect', 'VariantSwitch']:
                for parentPath in parentPaths:
                    variantSetName = self.parameter('variantSetName').getValue()
                    variantSelected = self.parameter('variantSelected').getValue()
                    current = '{%s=%s}' % (variantSetName, variantSelected)
                    if parentPath.endswith(current):
                        self.addPrimPath(parentPath)
                    else:
                        self.addPrimPath(self._combinePaths(parentPath, current))
            else:
                for parentPath in parentPaths:
                    self.addPrimPath(parentPath)


class MetadataNode(UsdNode):
    _metadataNodeMap = {}
    nodeType = '_Metadata'
    metadataKeys = []
    fillNormalColor = (50, 60, 50)
    borderNormalColor = (200, 150, 150, 200)

    @classmethod
    def getLiveUpdateParameterNames(cls):
        return cls.metadataKeys

    @classmethod
    def registerNode(cls, nodeObjectClass):
        super(MetadataNode, cls).registerNode(nodeObjectClass)
        for key in nodeObjectClass.metadataKeys:
            cls._metadataNodeMap.update({key: nodeObjectClass})

    @classmethod
    def getIgnorePrimInfoKeys(cls):
        return list(cls._metadataNodeMap.keys())

    @classmethod
    def getNodes(cls):
        return list(cls._metadataNodeMap.values())

    @classmethod
    def getMetadataNodeClass(cls, key):
        return cls._metadataNodeMap.get(key)

    def initMetadataParameters(self):
        pass

    def _initParameters(self):
        super(MetadataNode, self)._initParameters()
        self.initMetadataParameters()

    def _execute(self, stage, prim):
        params = self.getExecuteParams()
        for param in params:
            paramName = param.name()
            prim.SetMetadata(paramName, param.getValue())

        return stage, prim


class _PrimNode(UsdNode):
    nodeType = 'Prim'
    liveUpdateParameterNames = ['primName']

    @classmethod
    def getIgnorePrimInfoKeys(cls):
        keys = [
            'variantSetNames',
            'variantSelection',
            'payload',
            'references',
            'apiSchemas',  # not support
            'specifier',
        ]
        registerMetadatas = MetadataNode.getIgnorePrimInfoKeys()
        keys.extend(registerMetadatas)
        return keys

    def _initParameters(self):
        super(_PrimNode, self)._initParameters()
        self.addParameter('primName', 'string', builtIn=True)

    def _syncParameters(self):
        super(_PrimNode, self)._syncParameters()
        if self._primSpec is not None:
            self.parameter('primName').setValueQuietly(self._primSpec.name)

            for key in self._primSpec.ListInfoKeys():
                if key in self.getIgnorePrimInfoKeys():
                    continue
                # param = self.addParameter(key, )  # metadata value type?
                param = self.parameter(key)
                value = self._primSpec.GetInfo(key)
                if param is not None:
                    if value != param.getInheritValue():
                        param.setValueQuietly(value)
                else:
                    self.setMetadata(key, value)

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

        for key in self.getMetadataKeys():
            newPrim.SetMetadata(key, self.getMetadataValue(key))

        return stage, newPrim


class _PrimOnlyNode(_PrimNode):
    _ignoreExecuteParamNames = ['primName']
    liveUpdateParameterNames = ['primName', 'typeName', 'kind']

    def _initParameters(self):
        super(_PrimOnlyNode, self)._initParameters()
        self.addParameter('typeName', 'string', builtIn=True)
        self.addParameter('kind', 'string', builtIn=True)
        self.addParameter('instanceable', 'bool', builtIn=True)
        # self.addParameter('active', 'bool', defaultValue=True, builtIn=True)

    def _execute(self, stage, prim):
        stage, newPrim = super(_PrimOnlyNode, self)._execute(stage, prim)

        params = self.getExecuteParams()
        for param in params:
            paramName = param.name()
            newPrim.SetMetadata(paramName, param.getValue())

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
        self.addParameter('layerPath', 'string', builtIn=True)
        # self.addParameter('layerOffset', 'float', defaultValue=0.0, builtIn=True)
        # self.addParameter('layerScale', 'float', defaultValue=1.0, builtIn=True)

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
    liveUpdateParameterNames = [
        'defaultPrim', 'upAxis',
        'startTimeCode', 'endTimeCode'
    ]

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
                    self.setMetadata(key, value)

    def _initParameters(self):
        super(RootNode, self)._initParameters()
        self.addParameter('defaultPrim', 'string', builtIn=True)
        self.addParameter('upAxis', 'choose', builtIn=True, hints={'options': ['X', 'Y', 'Z']})
        self.addParameter('startTimeCode', 'float', label='Start', builtIn=True)
        self.addParameter('endTimeCode', 'float', label='End', builtIn=True)

    def _execute(self, stage, prim):
        rootPrim = stage.GetPrimAtPath('/')
        # rootLayer = stage.GetRootLayer()

        params = self.getExecuteParams()
        for param in params:
            paramName = param.name()
            rootPrim.SetMetadata(paramName, param.getValue())

        for key in self.getMetadataKeys():
            rootPrim.SetMetadata(key, self.getMetadataValue(key))

        return stage, rootPrim


class PrimDefineNode(_PrimOnlyNode):
    nodeType = 'PrimDefine'
    nodeGroup = 'Prim'
    fillNormalColor = (50, 60, 70)
    borderNormalColor = (200, 250, 200, 200)

    def _execute(self, stage, prim):
        stage, prim = super(PrimDefineNode, self)._execute(stage, prim)

        prim.SetMetadata('specifier', Sdf.SpecifierDef)

        return stage, prim


class PrimOverrideNode(_PrimOnlyNode):
    nodeType = 'PrimOverride'
    nodeGroup = 'Prim'
    fillNormalColor = (50, 60, 70)
    borderNormalColor = (200, 200, 250, 200)


class _RefNode(UsdNode):
    nodeType = '_Ref'
    nodeGroup = 'Meta'
    fillNormalColor = (60, 60, 100)
    borderNormalColor = (200, 150, 150, 200)
    liveUpdateParameterNames = [
        'assetPath', 'primPath'
        'layerOffset', 'layerScale'
    ]

    def _initParameters(self):
        super(_RefNode, self)._initParameters()
        self.addParameter('op', 'choose', defaultValue=LIST_EDITOR_PROXY_EXPLICIT_OP,
                          builtIn=True, hints={'options': LIST_EDITOR_PROXY_OPS})
        self.addParameter('assetPath', 'string', defaultValue='', builtIn=True)
        self.addParameter('primPath', 'string', defaultValue='', builtIn=True)
        self.addParameter('layerOffset', 'float', defaultValue=0.0, builtIn=True)
        self.addParameter('layerScale', 'float', defaultValue=1.0, builtIn=True)

    def __init__(self, reference=None, op=None, *args, **kwargs):
        self._reference = reference
        self._op = op
        super(_RefNode, self).__init__(*args, **kwargs)

    def _syncParameters(self):
        super(_RefNode, self)._syncParameters()
        if self._reference is not None:
            self._setParametersFromRef(self._reference)
        if self._op is not None:
            self.parameter('op').setValueQuietly(self._op)

    def _setTags(self):
        super(_RefNode, self)._setTags()
        self.item.addTag(self.nodeType, PixmapTag('{}.png'.format(self.nodeType)), position=0.25)

    def _setParametersFromRef(self, reference):
        if reference.assetPath != '':
            self.parameter('assetPath').setValueQuietly(reference.assetPath)
        if reference.primPath.pathString != '':
            self.parameter('primPath').setValueQuietly(reference.primPath.pathString)
        if reference.layerOffset.offset != 0:
            self.parameter('layerOffset').setValueQuietly(reference.layerOffset.offset)
        if reference.layerOffset.scale != 1:
            self.parameter('layerScale').setValueQuietly(reference.layerOffset.scale)

    def _getLayerOffset(self):
        layerOffset = self.parameter('layerOffset').getValue()
        layerScale = self.parameter('layerScale').getValue()

        layerOffset = Sdf.LayerOffset(offset=layerOffset, scale=layerScale)

        return layerOffset


class ReferenceNode(_RefNode):
    nodeType = 'Reference'

    def _execute(self, stage, prim):
        op = self.parameter('op').getValue()
        assetPath = self.parameter('assetPath').getValue()
        primPath = self.parameter('primPath').getValue()

        if primPath != '':
            reference = Sdf.Reference(assetPath, primPath, layerOffset=self._getLayerOffset())
        else:
            reference = Sdf.Reference(assetPath, layerOffset=self._getLayerOffset())

        # prim.GetReferences().SetReferences([reference])

        for currentPath in self.getPrimPath():
            primSpec = stage.GetRootLayer().GetPrimAtPath(currentPath)
            items = getattr(primSpec.referenceList, '{}Items'.format(op))
            items.append(reference)

        return stage, prim


class PayloadNode(_RefNode):
    nodeType = 'Payload'
    fillNormalColor = (100, 60, 100)

    def _execute(self, stage, prim):
        op = self.parameter('op').getValue()
        assetPath = self.parameter('assetPath').getValue()
        primPath = self.parameter('primPath').getValue()

        if primPath != '':
            payload = Sdf.Payload(assetPath, primPath, layerOffset=self._getLayerOffset())
        else:
            payload = Sdf.Payload(assetPath, layerOffset=self._getLayerOffset())

        # prim.SetPayload(payload)
        for currentPath in self.getPrimPath():
            primSpec = stage.GetRootLayer().GetPrimAtPath(currentPath)
            items = getattr(primSpec.payloadList, '{}Items'.format(op))
            items.append(payload)

        return stage, prim


class _AttributeNode(UsdNode):
    onlyAttrList = []
    ignoreAttrList = []

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

    def _generateParamLabel(self, name):
        return name

    def _addAttributeParameter(self, attribute):
        attributeName = attribute.name
        attributeType = str(attribute.typeName)
        needed = self._checkIsAttrNeeded(attributeName)
        if not needed:
            return

        param = self.addParameter(
            attributeName, attributeType,
            label=self._generateParamLabel(attributeName)
        )
        if param is not None:
            for key in attribute.ListInfoKeys():
                if key not in [
                    'typeName',
                    'default',
                    'timeSamples',
                    'connectionPaths',
                ]:
                    param.setMetadata(key, attribute.GetInfo(key))

            if attribute.HasInfo('connectionPaths'):
                connectionPathList = attribute.connectionPathList.GetAddedOrExplicitItems()
                connect = connectionPathList[0]
                param.setConnectQuietly(connect.pathString)
            elif attribute.HasInfo('timeSamples'):
                param.setTimeSamplesQuietly(attribute.GetInfo('timeSamples'))
            else:
                value = attribute.default
                param.setValueQuietly(value)

    def _setPrimAttributeFromParameter(self, prim, parameter):
        attrName = parameter.name()
        if not prim.HasAttribute(attrName):
            attribute = prim.CreateAttribute(attrName, parameter.valueTypeName)
        else:
            attribute = prim.GetAttribute(attrName)

        for key in parameter.getMetadataKyes():
            attribute.SetMetadata(key, parameter.getMetadataValue(key))
        if not parameter.hasMetadata('custom'):
            attribute.SetMetadata('custom', False)

        if parameter.hasConnect():
            attribute.SetConnections([parameter.getConnect()])
        elif parameter.hasKey():
            for time, value in parameter.getTimeSamples().items():
                attribute.Set(value, time)
        else:
            value = parameter.getValue()
            if value is not None:
                attribute.Set(value)

    def _attrParamChanged(self, parameter):
        if parameter.name() not in self.getIgnoreExecuteParamNames():
            attrName = parameter.name()
            for primPath in self._primPaths:
                prim = self._stage.GetPrimAtPath(primPath)
                if not prim.IsValid():
                    continue
                self._setPrimAttributeFromParameter(prim, parameter)

    def _execute(self, stage, prim):
        params = self.getExecuteParams()
        for param in params:
            self._setPrimAttributeFromParameter(prim, param)
        return stage, prim


class _PrimAttributeNode(_PrimNode, _AttributeNode):
    _ignoreExecuteParamNames = ['primName']
    typeName = None

    @classmethod
    def getIgnorePrimInfoKeys(cls):
        keys = []
        keys.extend(super(_PrimAttributeNode, cls).getIgnorePrimInfoKeys())
        keys.append('typeName')
        return keys

    def _syncParameters(self):
        super(_PrimAttributeNode, self)._syncParameters()
        if self._primSpec is not None:
            for name, attribute in self._primSpec.attributes.items():
                self._addAttributeParameter(attribute)

    def _execute(self, stage, prim):
        stage, newPrim = super(_PrimAttributeNode, self)._execute(stage, prim)
        stage, newPrim = _AttributeNode._execute(self, stage, newPrim)
        newPrim.SetMetadata('typeName', self.typeName)
        newPrim.SetMetadata('specifier', Sdf.SpecifierDef)

        return stage, newPrim


class AttributeSetNode(_AttributeNode):
    nodeType = 'AttributeSet'
    nodeGroup = 'Attribute'
    fillNormalColor = (50, 70, 60)
    borderNormalColor = (250, 250, 250, 200)
    onlyAttrList = []
    ignoreAttrList = [
        [ATTR_CHECK_OP.START, 'xformOp'],
    ]

    def _syncParameters(self):
        super(AttributeSetNode, self)._syncParameters()
        if self._primSpec is not None:
            for name, attribute in self._primSpec.attributes.items():
                self._addAttributeParameter(attribute)

    def _whenParamterValueChanged(self, parameter):
        super(AttributeSetNode, self)._whenParamterValueChanged(parameter)
        self._attrParamChanged(parameter)


class TransformNode(AttributeSetNode):
    nodeType = 'Transform'
    nodeGroup = 'Attribute'
    fillNormalColor = (60, 80, 70)
    borderNormalColor = (250, 250, 250, 200)
    onlyAttrList = [
        [ATTR_CHECK_OP.START, 'xformOp']
    ]
    ignoreAttrList = []

    def _initParameters(self):
        super(TransformNode, self)._initParameters()
        self.addParameter(
            'xformOp:translate', 'float3',
            defaultValue=Vec3fParameter.convertValueFromPy([0, 0, 0]),
            label='Translate', builtIn=True
        )
        self.addParameter(
            'xformOp:rotateXYZ', 'float3',
            defaultValue=Vec3fParameter.convertValueFromPy([0, 0, 0]),
            label='Rotate', builtIn=True
        )
        self.addParameter(
            'xformOp:scale', 'float3',
            defaultValue=Vec3fParameter.convertValueFromPy([1, 1, 1]),
            label='Scale', builtIn=True
        )
        self.addParameter(
            'xformOpOrder', 'token[]',
            defaultValue=TokenArrayParameter.convertValueFromPy([
                'xformOp:translate', 'xformOp:rotateXYZ', 'xformOp:scale'
            ]), label='Order', builtIn=True
        )

    def _generateParamLabel(self, name):
        return name.replace('xformOp:', '')

    def _syncParameters(self):
        super(TransformNode, self)._syncParameters()
        for primPath in self._primPaths:
            prim = self._stage.GetPrimAtPath(primPath)
            # for attr in prim.GetAttributes():
            #     print attr, type(attr)


class RelationshipSetNode(_AttributeNode):
    nodeType = 'RelationshipSet'
    nodeGroup = 'Relationship'
    fillNormalColor = (70, 60, 50)
    borderNormalColor = (250, 250, 250, 200)
    onlyAttrList = []
    ignoreAttrList = [
        [ATTR_CHECK_OP.START, 'material:binding'],
    ]

    def _syncParameters(self):
        super(RelationshipSetNode, self)._syncParameters()
        if self._primSpec is not None:
            for key, relationship in self._primSpec.relationships.items():
                self._addRelationshipParameter(relationship)

    def _addRelationshipParameter(self, relationship):
        relationshipName = relationship.name
        needed = self._checkIsAttrNeeded(relationshipName)
        if not needed:
            return

        targetPathList = [i.pathString for i in relationship.targetPathList.GetAddedOrExplicitItems()]

        param = self.addParameter(relationshipName, 'string[]')
        if param is not None:
            if param.parameterTypeString == 'string':
                param.setValueQuietly(targetPathList[0])
            else:
                param.setValueQuietly(targetPathList)

    def _setRelationshipOnPrim(self, prim, param):
        # print(param.name(), param.getValue(), param.hasKey())
        relationshipName = param.name()
        if not prim.HasRelationship(relationshipName):
            relationship = prim.CreateRelationship(relationshipName)
            relationship.SetCustom(False)
        else:
            relationship = prim.GetRelationship(relationshipName)

        value = param.getValue()
        if isinstance(value, basestring):
            value = [value]
        relationship.SetTargets(value)

    def _execute(self, stage, prim):
        params = self.getExecuteParams()
        for param in params:
            self._setRelationshipOnPrim(prim, param)
        return stage, prim


class MaterialAssignNode(RelationshipSetNode):
    nodeType = 'MaterialAssign'
    fillNormalColor = (50, 60, 80)
    borderNormalColor = (250, 250, 250, 200)
    onlyAttrList = [
        [ATTR_CHECK_OP.START, 'material:binding'],
    ]
    ignoreAttrList = []

    def _initParameters(self):
        super(MaterialAssignNode, self)._initParameters()
        self.addParameter(
            'material:binding', 'string',
            defaultValue='',
            label='Material', builtIn=True
        )
        self.addParameter(
            'material:binding:preview', 'string',
            defaultValue='',
            label='Preview', builtIn=True
        )
        self.addParameter(
            'material:binding:full', 'string',
            defaultValue='',
            label='Full', builtIn=True
        )

    def _generateParamLabel(self, name):
        return name.replace('material:', '')


class _VariantNode(UsdNode):
    nodeType = '_Variant'
    nodeGroup = 'Variant'
    fillNormalColor = (50, 60, 70)
    borderNormalColor = (200, 200, 150)


class VariantSetNode(_VariantNode):
    nodeType = 'VariantSet'
    liveUpdateParameterNames = [
        'variantSetName', 'variantList',
    ]

    def __init__(self, variantSetName=None, options=None, *args, **kwargs):
        super(VariantSetNode, self).__init__(*args, **kwargs)

        self.item.addTag('VariantSet', PixmapTag('VariantSet.png'), position=0.25)

        if variantSetName is not None:
            self.parameter('variantSetName').setValueQuietly(variantSetName)
        if options is not None:
            self.parameter('variantList').setValueQuietly(options)

    def _initParameters(self):
        super(VariantSetNode, self)._initParameters()
        self.addParameter('variantSetName', 'string', builtIn=True)
        self.addParameter('variantList', 'string[]', defaultValue=[], builtIn=True)

    def _execute(self, stage, prim):
        variantSetName = self.parameter('variantSetName').getValue()
        variantList = self.parameter('variantList').getValue()

        variantSet = prim.GetVariantSets().AddVariantSet(variantSetName)
        for variant in variantList:
            variantSet.AddVariant(variant)

        return stage, prim


class VariantSelectNode(_VariantNode):
    nodeType = 'VariantSelect'
    liveUpdateParameterNames = [
        'variantSetName', 'variantSelected',
    ]

    def __init__(self, variantSetName='', variantSelected='', options=None, *args, **kwargs):
        super(VariantSelectNode, self).__init__(*args, **kwargs)

        self.item.addTag('VariantSelect', PixmapTag('VariantSelect.png'), position=0.25)

        self.parameter('variantSetName').setValueQuietly(variantSetName)
        self.parameter('variantSelected').setValueQuietly(variantSelected)
        if options is not None:
            self.parameter('variantSelected').addOptions(options)

    def _initParameters(self):
        super(VariantSelectNode, self)._initParameters()
        self.addParameter('variantSetName', 'string', builtIn=True)
        self.addParameter('variantSelected', 'choose', builtIn=True)

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

        if variantSelected is not None:
            variantSet = prim.GetVariantSet(variantSetName)
            variantSet.SetVariantSelection(variantSelected)

        return stage, prim


class VariantSwitchNode(_VariantNode):
    nodeType = 'VariantSwitch'
    liveUpdateParameterNames = [
        'variantSetName', 'variantSelected',
    ]

    def __init__(self, variantSetName='', variantSelected='', *args, **kwargs):
        super(VariantSwitchNode, self).__init__(*args, **kwargs)

        self.item.addTag('VariantSwitch', PixmapTag('VariantSwitch.png'), position=0.25)

        self.parameter('variantSetName').setValueQuietly(variantSetName)
        self.parameter('variantSelected').setValueQuietly(variantSelected)

    def _initParameters(self):
        super(VariantSwitchNode, self)._initParameters()
        self.addParameter('variantSetName', 'string', builtIn=True)
        self.addParameter('variantSelected', 'string', builtIn=True)

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


Node.registerNode(LayerNode)
Node.registerNode(RootNode)
Node.registerNode(PrimDefineNode)
Node.registerNode(PrimOverrideNode)
Node.registerNode(ReferenceNode)
Node.registerNode(PayloadNode)

Node.registerNode(AttributeSetNode)
Node.registerNode(TransformNode)
Node.registerNode(RelationshipSetNode)
Node.registerNode(MaterialAssignNode)

Node.registerNode(VariantSetNode)
Node.registerNode(VariantSelectNode)
Node.registerNode(VariantSwitchNode)

Node.setParamDefault(LayerNode.nodeType, 'label', '[python os.path.basename("[value layerPath]")]')
Node.setParamDefault(RootNode.nodeType, 'label', '/')
Node.setParamDefault(PrimDefineNode.nodeType, 'label', '/[value primName]')
Node.setParamDefault(PrimOverrideNode.nodeType, 'label', '/[value primName]')
Node.setParamDefault(ReferenceNode.nodeType, 'label', '[python os.path.basename("[value assetPath]")]')
Node.setParamDefault(PayloadNode.nodeType, 'label', '[python os.path.basename("[value assetPath]")]')

Node.setParamDefault(MaterialAssignNode.nodeType, 'label', '[python os.path.basename("[value material:binding]")]')

Node.setParamDefault(VariantSetNode.nodeType, 'label', '{[value variantSetName]:[value variantList]}')
Node.setParamDefault(VariantSelectNode.nodeType, 'label', '{[value variantSetName]=[value variantSelected]}')
Node.setParamDefault(VariantSwitchNode.nodeType, 'label', '{[value variantSetName]?=[value variantSelected]}')


