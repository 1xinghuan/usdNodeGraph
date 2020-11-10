# -*- coding: utf-8 -*-

from .node import Node
from .usdNode import UsdNode, MaterialAssignNode
from ..cel.core import resolveCELString, COLLECTION_TYPE_NAME


class CollectionCreateNode(UsdNode):
    nodeType = 'CollectionCreate'
    nodeGroup = 'Custom'
    fillNormalColor = (7, 100, 50)
    borderNormalColor = (220, 250, 150)

    def _initParameters(self):
        super(CollectionCreateNode, self)._initParameters()
        self.addParameter('collectionName', 'string', label='name', builtIn=True)
        self.addParameter('CEL', 'string[]', builtIn=True)

    def _execute(self, stage, prim):
        collectionName = self.parameter('collectionName').getValue()
        cel = self.parameter('CEL').getValue()

        if collectionName == '':
            return stage, prim

        prim = stage.DefinePrim('/collection/{}'.format(collectionName))
        prim.SetMetadata('typeName', COLLECTION_TYPE_NAME)
        attribute = prim.CreateAttribute(
            'CEL',
            self.parameter('CEL').valueTypeName
        )
        attribute.Set(cel)

        return stage, prim


class MaterialAssign2Node(MaterialAssignNode):
    nodeType = 'MaterialAssign2'
    nodeGroup = 'Custom'
    borderNormalColor = (220, 250, 150)
    _ignoreExecuteParamNames = ['CEL']

    def _initParameters(self):
        super(MaterialAssign2Node, self)._initParameters()
        self.addParameter('CEL', 'string[]', builtIn=True)

    def _execute(self, stage, prim):
        cels = self.parameter('CEL').getValue()
        params = self.getExecuteParams()

        for cel in cels:
            for path in resolveCELString(cel, stage=stage):
                p = stage.GetPrimAtPath(path)
                if p.IsValid():
                    for param in params:
                        self._setRelationshipOnPrim(p, param)

        return stage, prim


Node.registerNode(CollectionCreateNode)
Node.registerNode(MaterialAssign2Node)
