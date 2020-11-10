from usdNodeGraph.core.parameter.basic import Parameter
from .param_widget import *


Parameter.registerParameter(StringParameter)
Parameter.registerParameter(ChooseParameter)
Parameter.registerParameter(TokenParameter)
Parameter.registerParameter(FilePathParameter)
Parameter.registerParameter(AssetParameter)
Parameter.registerParameter(TextParameter)
Parameter.registerParameter(BoolParameter)
Parameter.registerParameter(IntParameter)
Parameter.registerParameter(FloatParameter)
Parameter.registerParameter(DoubleParameter)
Parameter.registerParameter(Vec2fParameter)
Parameter.registerParameter(Vec3fParameter)
Parameter.registerParameter(Vec4fParameter)
Parameter.registerParameter(Vec2dParameter)
Parameter.registerParameter(Vec3dParameter)
Parameter.registerParameter(Vec4dParameter)
Parameter.registerParameter(Vec2hParameter)
Parameter.registerParameter(Vec3hParameter)
Parameter.registerParameter(Vec4hParameter)
Parameter.registerParameter(Color3fParameter)
Parameter.registerParameter(Color4fParameter)
Parameter.registerParameter(Point3fParameter)
Parameter.registerParameter(Normal3fParameter)
Parameter.registerParameter(Vector3fParameter)
Parameter.registerParameter(QuatdParameter)
Parameter.registerParameter(QuatfParameter)
Parameter.registerParameter(QuathParameter)
Parameter.registerParameter(Matrix2dParameter)
Parameter.registerParameter(Matrix3dParameter)
Parameter.registerParameter(Matrix4dParameter)
Parameter.registerParameter(TexCoord2fParameter)
Parameter.registerParameter(TexCoord2dParameter)
Parameter.registerParameter(TexCoord2hParameter)
Parameter.registerParameter(StringArrayParameter)
Parameter.registerParameter(TokenArrayParameter)
Parameter.registerParameter(IntArrayParameter)
Parameter.registerParameter(FloatArrayParameter)
Parameter.registerParameter(DoubleArrayParameter)
Parameter.registerParameter(Vec2fArrayParameter)
Parameter.registerParameter(Vec3fArrayParameter)
Parameter.registerParameter(Vec4fArrayParameter)
Parameter.registerParameter(Vec2dArrayParameter)
Parameter.registerParameter(Vec3dArrayParameter)
Parameter.registerParameter(Vec4dArrayParameter)
Parameter.registerParameter(Vec2hArrayParameter)
Parameter.registerParameter(Vec3hArrayParameter)
Parameter.registerParameter(Vec4hArrayParameter)
Parameter.registerParameter(Color3fArrayParameter)
Parameter.registerParameter(Point3fArrayParameter)
Parameter.registerParameter(Normal3fArrayParameter)
Parameter.registerParameter(QuatdArrayParameter)
Parameter.registerParameter(QuatfArrayParameter)
Parameter.registerParameter(QuathArrayParameter)
Parameter.registerParameter(Matrix2dArrayParameter)
Parameter.registerParameter(Matrix3dArrayParameter)
Parameter.registerParameter(Matrix4dArrayParameter)
Parameter.registerParameter(TexCoord2fArrayParameter)
Parameter.registerParameter(TexCoord2dArrayParameter)
Parameter.registerParameter(TexCoord2hArrayParameter)


Parameter.registerParameterWidget('string', StringParameterWidget)
Parameter.registerParameterWidget('choose', ChooseParameterWidget)
Parameter.registerParameterWidget('text', TextParameterWidget)
Parameter.registerParameterWidget('boolean', BoolParameterWidget)
Parameter.registerParameterWidget('integer', IntParameterWidget)
Parameter.registerParameterWidget('floating', FloatParameterWidget)

Parameter.registerParameterWidget('vec2f', Vec2fParameterWidget)
Parameter.registerParameterWidget('vec3f', Vec3fParameterWidget)
Parameter.registerParameterWidget('vec4f', Vec4fParameterWidget)
Parameter.registerParameterWidget('color', Color3fParameterWidget)
Parameter.registerParameterWidget('color3f', Color3fParameterWidget)
Parameter.registerParameterWidget('color4f', Color4fParameterWidget)
Parameter.registerParameterWidget('matrix2d', Matrix2dParameterWidget)
Parameter.registerParameterWidget('matrix3d', Matrix3dParameterWidget)
Parameter.registerParameterWidget('matrix4d', Matrix4dParameterWidget)

Parameter.registerParameterWidget('token[]', TokenArrayParameterWidget)
Parameter.registerParameterWidget('int[]', IntArrayParameterWidget)
Parameter.registerParameterWidget('float[]', FloatArrayParameterWidget)
Parameter.registerParameterWidget('vec2f[]', Vec2fArrayParameterWidget)
Parameter.registerParameterWidget('vec3f[]', Vec3fArrayParameterWidget)
Parameter.registerParameterWidget('vec4f[]', Vec4fArrayParameterWidget)
Parameter.registerParameterWidget('matrix2d[]', Matrix2dArrayParameterWidget)
Parameter.registerParameterWidget('matrix3d[]', Matrix3dArrayParameterWidget)
Parameter.registerParameterWidget('matrix4d[]', Matrix4dArrayParameterWidget)












