from .basic import Parameter
from pxr import Vt, Gf, Sdf


class _StringParameter(Parameter):
    valueDefault = ''


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
    def _convertValueToPy(cls, usdValue):
        if usdValue is not None:
            return usdValue.path

    @classmethod
    def _convertValueFromPy(cls, pyValue):
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


class _NonStringParameter(Parameter):
    @classmethod
    def _convertValueFromPy(cls, pyValue):
        if isinstance(pyValue, str):
            pyValue = eval(pyValue)
        return pyValue


class BoolParameter(_NonStringParameter):
    parameterTypeString = 'bool'
    valueTypeName = Sdf.ValueTypeNames.Bool
    valueDefault = False


class IntParameter(_NonStringParameter):
    parameterTypeString = 'int'
    valueTypeName = Sdf.ValueTypeNames.Int
    valueDefault = 0


class FloatParameter(_NonStringParameter):
    parameterTypeString = 'float'
    valueTypeName = Sdf.ValueTypeNames.Float
    valueDefault = 0


class DoubleParameter(_NonStringParameter):
    parameterTypeString = 'double'
    valueTypeName = Sdf.ValueTypeNames.Double
    valueDefault = 0


class _VecParamter(_NonStringParameter):
    _usdValueClass = None

    @classmethod
    def getValueDefault(cls):
        return cls._usdValueClass()

    @classmethod
    def _convertValueToPy(cls, usdValue):
        if usdValue is not None:
            return [i for i in usdValue]

    @classmethod
    def _convertValueFromPy(cls, pyValue):
        pyValue = super(_VecParamter, cls)._convertValueFromPy(pyValue)
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


class Vec2hParameter(_VecParamter):
    parameterTypeString = 'half2'
    valueTypeName = Sdf.ValueTypeNames.Half2
    _usdValueClass = Gf.Vec2h


class Vec3hParameter(_VecParamter):
    parameterTypeString = 'half3'
    valueTypeName = Sdf.ValueTypeNames.Half3
    _usdValueClass = Gf.Vec3h


class Vec4hParameter(_VecParamter):
    parameterTypeString = 'half4'
    valueTypeName = Sdf.ValueTypeNames.Half4
    _usdValueClass = Gf.Vec4h


class TexCoord2fParameter(_VecParamter):
    parameterTypeString = 'texCoord2f'
    valueTypeName = Sdf.ValueTypeNames.TexCoord2f
    _usdValueClass = Gf.Vec2f


class TexCoord2dParameter(_VecParamter):
    parameterTypeString = 'texCoord2d'
    valueTypeName = Sdf.ValueTypeNames.TexCoord2d
    _usdValueClass = Gf.Vec2d


class TexCoord2hParameter(_VecParamter):
    parameterTypeString = 'texCoord2h'
    valueTypeName = Sdf.ValueTypeNames.TexCoord2h
    _usdValueClass = Gf.Vec2h



class Color3fParameter(_VecParamter):
    parameterTypeString = 'color3f'
    valueTypeName = Sdf.ValueTypeNames.Color3f
    _usdValueClass = Gf.Vec3f


class Point3fParameter(_VecParamter):
    parameterTypeString = 'point3f'
    valueTypeName = Sdf.ValueTypeNames.Point3f
    _usdValueClass = Gf.Vec3f


class Normal3fParameter(_VecParamter):
    parameterTypeString = 'normal3f'
    valueTypeName = Sdf.ValueTypeNames.Normal3f
    _usdValueClass = Gf.Vec3f


class QuatParameter(_VecParamter):
    @classmethod
    def _convertValueToPy(cls, usdValue):
        if usdValue is not None:
            pyValue = []
            pyValue.append(usdValue.GetReal())
            pyValue.extend([i for i in usdValue.GetImaginary()])
            return pyValue


class QuatdParameter(QuatParameter):
    parameterTypeString = 'quatd'
    valueTypeName = Sdf.ValueTypeNames.Quatd
    _usdValueClass = Gf.Quatd
    valueDefault = Gf.Quatd()


class QuatfParameter(QuatParameter):
    parameterTypeString = 'quatf'
    valueTypeName = Sdf.ValueTypeNames.Quatf
    _usdValueClass = Gf.Quatf


class QuathParameter(QuatParameter):
    parameterTypeString = 'quath'
    valueTypeName = Sdf.ValueTypeNames.Quath
    _usdValueClass = Gf.Quath


class _MatrixParamter(_VecParamter):
    @classmethod
    def _convertValueToPy(cls, usdValue):
        if usdValue is not None:
            return [[i for i in vec] for vec in usdValue]

    @classmethod
    def _convertValueFromPy(cls, pyValue):
        pyValue = super(_MatrixParamter, cls)._convertValueFromPy(pyValue)
        if pyValue is not None:
            return cls._usdValueClass(pyValue)


class Matrix2dParameter(_MatrixParamter):
    parameterTypeString = 'matrix2d'
    valueTypeName = Sdf.ValueTypeNames.Matrix2d
    _usdValueClass = Gf.Matrix2d


class Matrix3dParameter(_MatrixParamter):
    parameterTypeString = 'matrix3d'
    valueTypeName = Sdf.ValueTypeNames.Matrix3d
    _usdValueClass = Gf.Matrix3d


class Matrix4dParameter(_MatrixParamter):
    parameterTypeString = 'matrix4d'
    valueTypeName = Sdf.ValueTypeNames.Matrix4d
    _usdValueClass = Gf.Matrix4d


# --------------------------------------- array ----------------------------------
class _ArrayParameter(_NonStringParameter):
    _usdValueClass = None

    @classmethod
    def getValueDefault(cls):
        return cls._usdValueClass()

    @classmethod
    def getChildParamType(cls):
        return cls.parameterTypeString.replace('[]', '')

    @classmethod
    def getChildParamClass(cls):
        paramClass = Parameter.getParameter(cls.getChildParamType())
        return paramClass

    @classmethod
    def _convertValueToPy(cls, usdValue):
        childParamClass = cls.getChildParamClass()
        return [childParamClass.convertValueToPy(i) for i in usdValue]

    @classmethod
    def _convertValueFromPy(cls, pyValue):
        pyValue = super(_ArrayParameter, cls)._convertValueFromPy(pyValue)
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


class Vec2hArrayParameter(_ArrayParameter):
    parameterTypeString = 'half2[]'
    valueTypeName = Sdf.ValueTypeNames.Half2Array
    _usdValueClass = Vt.Vec2hArray


class Vec3hArrayParameter(_ArrayParameter):
    parameterTypeString = 'half3[]'
    valueTypeName = Sdf.ValueTypeNames.Half3Array
    _usdValueClass = Vt.Vec3hArray


class Vec4hArrayParameter(_ArrayParameter):
    parameterTypeString = 'half4[]'
    valueTypeName = Sdf.ValueTypeNames.Half4Array
    _usdValueClass = Vt.Vec4hArray


class Color3fArrayParameter(_ArrayParameter):
    parameterTypeString = 'color3f[]'
    valueTypeName = Sdf.ValueTypeNames.Color3fArray
    _usdValueClass = Vt.Vec3fArray


class Point3fArrayParameter(_ArrayParameter):
    parameterTypeString = 'point3f[]'
    valueTypeName = Sdf.ValueTypeNames.Point3fArray
    _usdValueClass = Vt.Vec3fArray


class Normal3fArrayParameter(_ArrayParameter):
    parameterTypeString = 'normal3f[]'
    valueTypeName = Sdf.ValueTypeNames.Normal3fArray
    _usdValueClass = Vt.Vec3fArray


class QuatdArrayParameter(_ArrayParameter):
    parameterTypeString = 'quatd[]'
    valueTypeName = Sdf.ValueTypeNames.QuatdArray
    _usdValueClass = Vt.QuatdArray


class QuatfArrayParameter(_ArrayParameter):
    parameterTypeString = 'quatf[]'
    valueTypeName = Sdf.ValueTypeNames.QuatfArray
    _usdValueClass = Vt.QuatfArray


class QuathArrayParameter(_ArrayParameter):
    parameterTypeString = 'quath[]'
    valueTypeName = Sdf.ValueTypeNames.QuathArray
    _usdValueClass = Vt.QuathArray


class Matrix2dArrayParameter(_ArrayParameter):
    parameterTypeString = 'matrix2d[]'
    valueTypeName = Sdf.ValueTypeNames.Matrix2dArray
    _usdValueClass = Vt.Matrix2dArray


class Matrix3dArrayParameter(_ArrayParameter):
    parameterTypeString = 'matrix3d[]'
    valueTypeName = Sdf.ValueTypeNames.Matrix3dArray
    _usdValueClass = Vt.Matrix3dArray


class Matrix4dArrayParameter(_ArrayParameter):
    parameterTypeString = 'matrix4d[]'
    valueTypeName = Sdf.ValueTypeNames.Matrix4dArray
    _usdValueClass = Vt.Matrix4dArray


class TexCoord2fArrayParameter(_ArrayParameter):
    parameterTypeString = 'texCoord2f[]'
    valueTypeName = Sdf.ValueTypeNames.TexCoord2fArray
    _usdValueClass = Vt.Vec2fArray


class TexCoord2dArrayParameter(_ArrayParameter):
    parameterTypeString = 'texCoord2d[]'
    valueTypeName = Sdf.ValueTypeNames.TexCoord2dArray
    _usdValueClass = Vt.Vec2dArray


class TexCoord2hArrayParameter(_ArrayParameter):
    parameterTypeString = 'texCoord2h[]'
    valueTypeName = Sdf.ValueTypeNames.TexCoord2hArray
    _usdValueClass = Vt.Vec2hArray

