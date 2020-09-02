from pxr import Sdr


class SdrRegistry(object):
    _reg = None

    @classmethod
    def getRegistry(cls):
        if cls._reg is None:
            try:
                cls._reg = Sdr.Registry()
            except:
                pass
        return cls._reg

    @classmethod
    def getShaderNodeByName(cls, shaderName):
        if cls.getRegistry() is not None:
            return cls.getRegistry().GetShaderNodeByName(shaderName)
        else:
            return None

    @classmethod
    def getNodeNames(cls):
        if cls.getRegistry() is not None:
            return cls.getRegistry().GetNodeNames()
        else:
            return []


