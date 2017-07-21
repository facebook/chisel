#!/usr/bin/python

# Copyright (c) 2014, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

import lldb
import fblldbbase as fb

def isKindOfClass(obj, className):
  isKindOfClassStr = '[(id)' + obj + ' isKindOfClass:[{} class]]'
  return fb.evaluateBooleanExpression(isKindOfClassStr.format(className))

def className(obj):
  return fb.evaluateExpressionValue('(id)[(' + obj + ') class]').GetObjectDescription()
