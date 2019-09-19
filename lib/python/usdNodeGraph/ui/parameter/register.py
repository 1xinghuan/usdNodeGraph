
class ParameterRegister(object):
    _PARAMETER_MAP = {}

    @classmethod
    def registerParameter(cls, parameterClass, parameterWidget):
        typeName = parameterClass.parameterTypeString
        cls._PARAMETER_MAP.update({
            typeName: {
                'parameterClass': parameterClass,
                'parameterWidget': parameterWidget
            }
        })

    @classmethod
    def getParameter(cls, typeName):
        return cls._PARAMETER_MAP.get(typeName, {}).get('parameterClass')

    @classmethod
    def getParameterWidget(cls, typeName):
        return cls._PARAMETER_MAP.get(typeName, {}).get('parameterWidget')


from .parameter import *
from .param_widget import *


ParameterRegister.registerParameter(StringParameter, StringParameterWidget)
ParameterRegister.registerParameter(ChooseParameter, ChooseParameterWidget)
ParameterRegister.registerParameter(TokenParameter, StringParameterWidget)
ParameterRegister.registerParameter(FilePathParameter, StringParameterWidget)
ParameterRegister.registerParameter(AssetParameter, StringParameterWidget)
ParameterRegister.registerParameter(TextParameter, TextParameterWidget)
ParameterRegister.registerParameter(BoolParameter, BoolParameterWidget)

ParameterRegister.registerParameter(IntParameter, IntParameterWidget)
ParameterRegister.registerParameter(FloatParameter, FloatParameterWidget)
ParameterRegister.registerParameter(DoubleParameter, FloatParameterWidget)

ParameterRegister.registerParameter(Vec2fParameter, Vec2fParameterWidget)
ParameterRegister.registerParameter(Vec3fParameter, Vec3fParameterWidget)
ParameterRegister.registerParameter(Vec4fParameter, Vec4fParameterWidget)

ParameterRegister.registerParameter(Vec2dParameter, Vec2fParameterWidget)
ParameterRegister.registerParameter(Vec3dParameter, Vec3fParameterWidget)
ParameterRegister.registerParameter(Vec4dParameter, Vec4fParameterWidget)

ParameterRegister.registerParameter(Color3fParameter, Vec3fParameterWidget)
ParameterRegister.registerParameter(Point3fParameter, Vec3fParameterWidget)


ParameterRegister.registerParameter(StringArrayParameter, TokenArrayParameterWidget)
ParameterRegister.registerParameter(TokenArrayParameter, TokenArrayParameterWidget)
ParameterRegister.registerParameter(IntArrayParameter, IntArrayParameterWidget)
ParameterRegister.registerParameter(FloatArrayParameter, FloatArrayParameterWidget)
ParameterRegister.registerParameter(DoubleArrayParameter, FloatArrayParameterWidget)
ParameterRegister.registerParameter(Vec2fArrayParameter, Vec2fArrayParameterWidget)
ParameterRegister.registerParameter(Vec3fArrayParameter, Vec3fArrayParameterWidget)
ParameterRegister.registerParameter(Vec4fArrayParameter, Vec4fArrayParameterWidget)
ParameterRegister.registerParameter(Vec2dArrayParameter, Vec2fArrayParameterWidget)
ParameterRegister.registerParameter(Vec3dArrayParameter, Vec3fArrayParameterWidget)
ParameterRegister.registerParameter(Vec4dArrayParameter, Vec4fArrayParameterWidget)
ParameterRegister.registerParameter(Color3fArrayParameter, Vec3fArrayParameterWidget)
ParameterRegister.registerParameter(Point3fArrayParameter, Vec3fArrayParameterWidget)
