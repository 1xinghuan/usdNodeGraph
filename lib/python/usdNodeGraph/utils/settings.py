# -*- coding: utf-8 -*-

import os
from os.path import join as opj
from usdNodeGraph.module.sqt import QtCore, to_unicode
import sys

PY_MAIN_VERSION = sys.version_info[0]

if PY_MAIN_VERSION == 3:
    from imp import reload
    basestring = str
    unicode = str
    long = int
else:
    reload = reload
    basestring = basestring


User_Setting = QtCore.QSettings(
    opj(
        os.path.expanduser('~'),
        '.usd',
        'nodegraph.ini')
    , QtCore.QSettings.IniFormat
)


def get_user_setting(setting='sins'):
    return QtCore.QSettings(opj(
        os.path.expanduser('~'),
        '.sins',
        '{}.ini'.format(setting)
    ), QtCore.QSettings.IniFormat)


def setting_to_unicode(setting):
    if isinstance(setting, basestring):
        return to_unicode(setting)
    else:
        return to_unicode(setting.toPyObject())


def setting_to_int(setting):
    if isinstance(setting, basestring):
        return int(setting)
    elif isinstance(setting, (int, long)):
        return setting
    else:
        return setting.toInt()[0]


def setting_to_int_list(setting):
    if isinstance(setting, list):
        return [int(i) for i in setting if i is not None]
    else:
        return [i.toInt()[0] for i in setting.toList()]


def setting_to_unicode_list(setting):
    if isinstance(setting, list):
        return setting
    elif isinstance(setting, basestring):
        return [setting]
    else:
        return [setting_to_unicode(i) for i in setting.toList()]


def setting_to_dict(setting):
    if isinstance(setting, dict):
        return setting
    else:
        temp = setting.toPyObject()
        result = dict()
        for item in temp.items():
            key = to_unicode(item[0])
            value = item[1]
            if not (isinstance(value, (int, long, list, basestring)) or value is None):
                value = to_unicode(value)
            result.update({key: value})
        return result


def setting_to_dict_list(setting):
    if isinstance(setting, list):
        return setting
    else:
        return [setting_to_dict(i) for i in setting.toList()]


def setting_to_bytearray(setting):
    if isinstance(setting, QtCore.QByteArray):
        return setting
    else:
        return setting.toByteArray()


def convert_setting(setting, to_type='unicode'):
    func = 'setting_to_{}'.format(to_type)
    module_ = __import__(__name__, fromlist=[func])
    return getattr(module_, func)(setting)


def read_setting(from_setting, setting_name, default=None, to_type='unicode'):
    setting = from_setting.value(setting_name, default)
    if setting is not None:
        if to_type is None:
            return setting
        else:
            return convert_setting(setting, to_type)
    else:
        if default is None:
            if to_type == 'int':
                default = 0
            elif to_type == 'unicode':
                default = ''
            elif to_type == 'int_list':
                default = []
            elif to_type == 'unicode_list':
                default = []
            elif to_type == 'dict':
                default = {}
        return default


def write_setting(to_setting, setting_name, value):
    to_setting.setValue(setting_name, value)


def append_list_setting(to_setting, setting_name, to_type='unicode', value=None, max_count=1):
    if to_type == 'unicode':
        setting_string = read_setting(to_setting, setting_name, default='', to_type=to_type)
        old_list = setting_string.split(',')
    else:
        old_list = read_setting(to_setting, setting_name, default=list(), to_type=to_type)
    # old_list = list(set(old_list))
    if value in old_list:
        old_list.remove(value)
    old_list.insert(0, value)
    while len(old_list) > max_count:
        old_list.remove(old_list[max_count])
    result = old_list
    if to_type == 'unicode':
        result = ','.join(old_list)
    write_setting(to_setting, setting_name, result)

