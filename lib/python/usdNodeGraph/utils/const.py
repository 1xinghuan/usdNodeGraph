# -*- coding: utf-8 -*-

import os
import collections


def consts(**name_value_dict):
    ConstantContainer = collections.namedtuple(
        'ConstantContainer',
        list(name_value_dict.keys())
    )
    return ConstantContainer(**name_value_dict)


INPUT_ATTRIBUTE_PREFIX = 'inputs:'
OUTPUT_ATTRIBUTE_PREFIX = 'outputs:'


VIEWPORT_FULL_UPDATE = os.environ.get('USD_NODEGRAPH_VIEWPORT_FULL_UPDATE', '0')

