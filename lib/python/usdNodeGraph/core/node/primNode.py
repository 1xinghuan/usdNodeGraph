from .usdNode import PrimDefineNode, Node


class PrimDefineNode2(PrimDefineNode):
    def _initParameters(self):
        super(PrimDefineNode2, self)._initParameters()
        self.parameter('typeName').setVisible(False)

    def _execute(self, stage, prim):
        stage, newPrim = super(PrimDefineNode2, self)._execute(stage, prim)

        newPrim.SetMetadata('typeName', self.nodeType)

        return stage, newPrim


class XformNode(PrimDefineNode2):
    nodeType = 'Xform'


class ScopeNode(PrimDefineNode2):
    nodeType = 'Scope'


class CubeNode(PrimDefineNode2):
    nodeType = 'Cube'


class SphereNode(PrimDefineNode2):
    nodeType = 'Sphere'


class CylinderNode(PrimDefineNode2):
    nodeType = 'Cylinder'


class CapsuleNode(PrimDefineNode2):
    nodeType = 'Capsule'


class ConeNode(PrimDefineNode2):
    nodeType = 'Cone'


class MeshNode(PrimDefineNode2):
    nodeType = 'Mesh'


class PointInstancerNode(PrimDefineNode2):
    nodeType = 'PointInstancer'


class CameraNode(PrimDefineNode2):
    nodeType = 'Camera'


class VolumeNode(PrimDefineNode2):
    nodeType = 'Volume'


class OpenVDBAssetNode(PrimDefineNode2):
    nodeType = 'OpenVDBAsset'


class LightNode(PrimDefineNode2):
    nodeType = 'Light'


class DistantLightNode(PrimDefineNode2):
    nodeType = 'DistantLight'


class DiskLightNode(PrimDefineNode2):
    nodeType = 'DiskLight'


class RectLightNode(PrimDefineNode2):
    nodeType = 'RectLight'


class SphereLightNode(PrimDefineNode2):
    nodeType = 'SphereLight'


class CylinderLightNode(PrimDefineNode2):
    nodeType = 'CylinderLight'


class GeometryLightNode(PrimDefineNode2):
    nodeType = 'GeometryLight'


class DomeLightNode(PrimDefineNode2):
    nodeType = 'DomeLight'


for node in [
    XformNode,
    ScopeNode,
    CubeNode,
    SphereNode,
    CylinderNode,
    CapsuleNode,
    ConeNode,
    MeshNode,
    PointInstancerNode,
    CameraNode,
    VolumeNode,
    OpenVDBAssetNode,
    LightNode,
    DistantLightNode,
    DiskLightNode,
    RectLightNode,
    SphereLightNode,
    CylinderLightNode,
    GeometryLightNode,
    DomeLightNode,
]:
    Node.registerNode(node)
    Node.setParamDefault(node.nodeType, 'typeName', node.nodeType)

