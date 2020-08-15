from usdNodeGraph.module.sqt import QtCore


class GraphState(QtCore.QObject):
    currentTimeChanged = QtCore.Signal(float)

    _state = None
    _times = {}

    @classmethod
    def getState(cls):
        if cls._state is None:
            cls._state = cls()
        return cls._state

    @classmethod
    def getTimeState(cls, stage):
        if stage not in cls._times:
            cls._times[stage] = {
                'time': 0.0,
                'timeIn': 0.0,
                'timeOut': 0.0,
            }
        return cls._times[stage]

    @classmethod
    def setCurrentTime(cls, time, stage):
        cls.getTimeState(stage)['time'] = float(time)
        cls.getState().currentTimeChanged.emit(float(time))

    @classmethod
    def getCurrentTime(cls, stage):
        return cls.getTimeState(stage)['time']

    @classmethod
    def setTimeIn(cls, timeIn, stage):
        cls.getTimeState(stage)['timeIn'] = float(timeIn)

    @classmethod
    def getTimeIn(cls, stage):
        return cls.getTimeState(stage)['timeIn']

    @classmethod
    def setTimeOut(cls, timeOut, stage):
        cls.getTimeState(stage)['timeOut'] = float(timeOut)

    @classmethod
    def getTimeOut(cls, stage):
        return cls.getTimeState(stage)['timeOut']

