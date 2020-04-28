#!/usr/bin/python

# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import fbchisellldbbase as fb


def isKindOfClass(obj, className):
    isKindOfClassStr = "[(id)" + obj + " isKindOfClass:[{} class]]"
    return fb.evaluateBooleanExpression(isKindOfClassStr.format(className))


def className(obj):
    return fb.evaluateExpressionValue(
        "(id)[(" + obj + ") class]"
    ).GetObjectDescription()
