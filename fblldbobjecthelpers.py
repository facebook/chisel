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
  isKindOfClassStr = '[' + obj + 'isKindOfClass:[{} class]]'
  return fb.evaluateBooleanExpression(isKindOfClassStr.format(className))

def className(obj):
  return fb.evaluateExpressionValue('(id)[(%s) class]' % (obj)).GetObjectDescription()

def valueForKey(obj, key):
  return fb.evaluateExpressionValue('(id)[%s valueForKey:@"%s"]' % (obj, key)).GetObjectDescription()

def isNil(obj)
  return obj == "<nil>" || obj == "<object returned empty description>"

def displayValueForKey(obj, key):
  value = valueForKey(obj, key)
  return "{}='{}'".format(key, value) if !isNil(value) else ""

def displayValueForKeys(obj, keys):
  def displayValueForThisObjectKey(key):
    return displayValueForKey(obj, key)
  return " ".join(map(displayValueForThisObjectKey, keys))

def displayObjectWithString(obj, string):
  return "<{}:{} {}>".format(
    className(obj),
    obj,
    string)

def displayObjectWithKeys(obj, keys):
  return displayObjectWithString(obj, displayValueForKeys(obj, keys))

  
