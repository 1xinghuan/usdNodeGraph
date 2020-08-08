from .basic import Parameter
from pxr import Vt, Gf, Sdf


class _StringParameter(Parameter):
    pass


class StringParameter(_StringParameter):
    parameterTypeString = 'string'
    valueTypeName = Sdf.ValueTypeNames.String


class TokenParameter(_StringParameter):
    parameterTypeString = 'token'
    valueTypeName = Sdf.ValueTypeNames.Token


class FilePathParameter(_StringParameter):
    parameterTypeString = 'file'


class TextParameter(_StringParameter):
    parameterTypeString = 'text'


class AssetParameter(_StringParameter):
    parameterTypeString = 'asset'
    valueTypeName = Sdf.ValueTypeNames.Asset

    @classmethod
    def convertValueToPy(cls, usdValue):
        if usdValue is not None:
            return usdValue.path

    @classmethod
    def convertValueFromPy(cls, pyValue):
        if pyValue is not None:
            return Sdf.AssetPath(pyValue)


class ChooseParameter(_StringParameter):
    parameterTypeString = 'choose'

    def __init__(self, *args, **kwargs):
        super(ChooseParameter, self).__init__(*args, **kwargs)

        self._items = []

    def addItems(self, items):
        self._items.extend(items)

    def addItem(self, item):
        self._items.append(item)

    def getItems(self):
        return self._items


class BoolParameter(Parameter):
    parameterTypeString = 'bool'
    valueTypeName = Sdf.ValueTypeNames.Bool


class IntParameter(Parameter):
    parameterTypeString = 'int'
    valueTypeName = Sdf.ValueTypeNames.Int


class FloatParameter(Parameter):
    parameterTypeString = 'float'
    valueTypeName = Sdf.ValueTypeNames.Float


class DoubleParameter(Parameter):
    parameterTypeString = 'double'
    valueTypeName = Sdf.ValueTypeNames.Double


class _VecParamter(Parameter):
    _usdValueClass = None

    @classmethod
    def convertValueToPy(cls, usdValue):
        if usdValue is not None:
            return [i for i in usdValue]

    @classmethod
    def convertValueFromPy(cls, pyValue):
        if pyValue is not None:
            return cls._usdValueClass(*pyValue)


class Vec2fParameter(_VecParamter):
    parameterTypeString = 'float2'
    valueTypeName = Sdf.ValueTypeNames.Float2
    _usdValueClass = Gf.Vec2f


class Vec3fParameter(_VecParamter):
    parameterTypeString = 'float3'
    valueTypeName = Sdf.ValueTypeNames.Float3
    _usdValueClass = Gf.Vec3f


class Vec4fParameter(_VecParamter):
    parameterTypeString = 'float4'
    valueTypeName = Sdf.ValueTypeNames.Float4
    _usdValueClass = Gf.Vec4f


class Vec2dParameter(_VecParamter):
    parameterTypeString = 'double2'
    valueTypeName = Sdf.ValueTypeNames.Double2
    _usdValueClass = Gf.Vec2d


class Vec3dParameter(_VecParamter):
    parameterTypeString = 'double3'
    valueTypeName = Sdf.ValueTypeNames.Double3
    _usdValueClass = Gf.Vec3d


class Vec4dParameter(_VecParamter):
    parameterTypeString = 'double4'
    valueTypeName = Sdf.ValueTypeNames.Double4
    _usdValueClass = Gf.Vec4d


class Color3fParameter(_VecParamter):
    parameterTypeString = 'color3f'
    valueTypeName = Sdf.ValueTypeNames.Color3f
    _usdValueClass = Gf.Vec3f


class Point3fParameter(_VecParamter):
    parameterTypeString = 'point3f'
    valueTypeName = Sdf.ValueTypeNames.Point3f
    _usdValueClass = Gf.Vec3f



# --------------------------------------- array ----------------------------------
class _ArrayParameter(Parameter):
    _usdValueClass = None

    @classmethod
    def getChildParamType(cls):
        return cls.parameterTypeString.replace('[]', '')

    @classmethod
    def getChildParamClass(cls):
        from usdNodeGraph.ui.parameter.register import ParameterRegister

        paramClass = ParameterRegister.getParameter(cls.getChildParamType())
        return paramClass

    @classmethod
    def convertValueToPy(cls, usdValue):
        childParamClass = cls.getChildParamClass()
        return [childParamClass.convertValueToPy(i) for i in usdValue]

    @classmethod
    def convertValueFromPy(cls, pyValue):
        childParamClass = cls.getChildParamClass()
        return cls._usdValueClass([childParamClass.convertValueFromPy(i) for i in pyValue])


class StringArrayParameter(_ArrayParameter):
    parameterTypeString = 'string[]'
    valueTypeName = Sdf.ValueTypeNames.StringArray
    _usdValueClass = Vt.StringArray


class IntArrayParameter(_ArrayParameter):
    parameterTypeString = 'int[]'
    valueTypeName = Sdf.ValueTypeNames.IntArray
    _usdValueClass = Vt.IntArray


class TokenArrayParameter(_ArrayParameter):
    parameterTypeString = 'token[]'
    valueTypeName = Sdf.ValueTypeNames.TokenArray
    _usdValueClass = Vt.TokenArray


class FloatArrayParameter(_ArrayParameter):
    parameterTypeString = 'float[]'
    valueTypeName = Sdf.ValueTypeNames.FloatArray
    _usdValueClass = Vt.FloatArray


class DoubleArrayParameter(_ArrayParameter):
    parameterTypeString = 'double[]'
    valueTypeName = Sdf.ValueTypeNames.DoubleArray
    _usdValueClass = Vt.DoubleArray


class Vec2fArrayParameter(_ArrayParameter):
    parameterTypeString = 'float2[]'
    valueTypeName = Sdf.ValueTypeNames.Float2Array
    _usdValueClass = Vt.Vec2fArray


class Vec3fArrayParameter(_ArrayParameter):
    parameterTypeString = 'float3[]'
    valueTypeName = Sdf.ValueTypeNames.Float3Array
    _usdValueClass = Vt.Vec3fArray


class Vec4fArrayParameter(_ArrayParameter):
    parameterTypeString = 'float4[]'
    valueTypeName = Sdf.ValueTypeNames.Float4Array
    _usdValueClass = Vt.Vec4fArray


class Vec2dArrayParameter(_ArrayParameter):
    parameterTypeString = 'double2[]'
    valueTypeName = Sdf.ValueTypeNames.Double2Array
    _usdValueClass = Vt.Vec2dArray


class Vec3dArrayParameter(_ArrayParameter):
    parameterTypeString = 'double3[]'
    valueTypeName = Sdf.ValueTypeNames.Double3Array
    _usdValueClass = Vt.Vec3dArray


class Vec4dArrayParameter(_ArrayParameter):
    parameterTypeString = 'double4[]'
    valueTypeName = Sdf.ValueTypeNames.Double4Array
    _usdValueClass = Vt.Vec4dArray


class Color3fArrayParameter(_ArrayParameter):
    parameterTypeString = 'color3f[]'
    valueTypeName = Sdf.ValueTypeNames.Color3fArray
    _usdValueClass = Vt.Vec3fArray


class Point3fArrayParameter(_ArrayParameter):
    parameterTypeString = 'point3f[]'
    valueTypeName = Sdf.ValueTypeNames.Point3fArray
    _usdValueClass = Vt.Vec3fArray

