# -*- coding: utf-8 -*-

import logging
import inspect
import functools
import time
import sys
import os

LOG_LEVEL_ENV = os.environ.get('USD_NODEGRAPH_DEBUG_LEVEL', 'WARNING').upper()  # DEBUG/WARNING/ERROR
LOG_LEVEL = getattr(logging, LOG_LEVEL_ENV)
LOG_FORMATS = [
    '[%(levelname)s]:%(name)s: %(asctime)s %(pathname)s[line:%(lineno)d] %(funcName)s: %(message)s',
    '[%(levelname)s]:%(name)s: %(funcName)s: %(message)s',
    '[%(levelname)s]:%(name)s: %(asctime)s %(message)s',
]
LOGGERS = {}

# logging.basicConfig(level=LOG_LEVEL)
# logging.basicConfig(stream=sys.stdout)


def get_fomatter(format=0):
    dateFmt = '%d %b %Y %H:%M:%S'
    strFmt = LOG_FORMATS[format]
    formatter = logging.Formatter(strFmt, dateFmt)
    return formatter


def set_logger(logger, format=0):
    logger.setLevel(LOG_LEVEL)
    formatter = get_fomatter(format)
    # ch_handler = logging.StreamHandler(sys.stdout)
    chHandler = logging.StreamHandler()
    chHandler.setFormatter(formatter)
    logger.addHandler(chHandler)


def get_logger(name, format=1):
    global LOGGERS

    if name not in LOGGERS:
        logger = logging.getLogger(name)
        set_logger(logger, format)
        LOGGERS[name] = logger
    else:
        logger = LOGGERS[name]
    return logger


timeLogger = get_logger('log_cost_time', 2)


def log_cost_time(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # logger = get_logger('log_cost_time', 1)
        timeLogger.debug('Enter:%s %s' % (inspect.getmodule(func).__name__, func.__name__))
        start = time.time()
        u = func(*args, **kwargs)
        timeLogger.debug('Leave:%s cost time: %s' % (func.__name__, time.time() - start))
        return u
    return wrapper


def get_current_function_name():
    return inspect.stack()[1][3]
