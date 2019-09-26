from pxr import Sdr

class SdrRegistry(object):
    _reg = None

    @classmethod
    def getRegistry(cls):
        if cls._reg is None:
            cls._reg = Sdr.Registry()
        return cls._reg

    @classmethod
    def getShaderNodeByName(cls, shaderName):
        return cls.getRegistry().GetShaderNodeByName(shaderName)

    @classmethod
    def getNodeNames(cls):
        return cls.getRegistry().GetNodeNames()


