#!/usr/bin/python

# Copyright (c) 2014, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

import re

import lldb
import fblldbbase as fb

def objc_getClass(className):
  command = '(void*)objc_getClass("{}")'.format(className)
  value = fb.evaluateExpression(command)
  return value

def object_getClass(object):
  command = '(void*)object_getClass({})'.format(object)
  value = fb.evaluateExpression(command)
  return value

def class_getName(klass):
  command = '(const char*)class_getName((Class){})'.format(klass)
  value = fb.evaluateExpressionValue(command).GetSummary().strip('"')
  return value

def class_getSuperclass(klass):
  command = '(void*)class_getSuperclass((Class){})'.format(klass)
  value = fb.evaluateExpression(command)
  return value

def class_isMetaClass(klass):
    command = 'class_isMetaClass((Class){})'.format(klass)
    return fb.evaluateBooleanExpression(command)

def class_getInstanceMethod(klass, selector):
  command = '(void*)class_getInstanceMethod((Class){}, @selector({}))'.format(klass, selector)
  value = fb.evaluateExpression(command)
  return value

def currentArch():
  targetTriple = lldb.debugger.GetSelectedTarget().GetTriple()
  arch = targetTriple.split('-')[0]
  if arch == 'x86_64h':
    arch = 'x86_64'
  return arch

def functionPreambleExpressionForSelf():
  if currentArch() == 'i386':
    return '*(id*)($esp+4)'
  else:
    return '(id)$arg1'

def functionPreambleExpressionForObjectParameterAtIndex(parameterIndex):
  arch = currentArch()
  if arch == 'i386':
    return '*(id*)($esp+{offset})'.format(offset=12 + parameterIndex * 4)
  elif arch == 'x86_64' and parameterIndex > 3:
    raise Exception("Current implementation can not return object at index greater than 3 for x86_64")
  elif arch == 'arm64' and parameterIndex > 5:
    raise Exception("Current implementation can not return object at index greater than 5 for arm64")
  elif re.match(r'^armv.*$', arch) and parameterIndex > 1:
    raise Exception("Current implementation can not return object at index greater than 1 for arm32")
  return '(id)$arg{n}'.format(n=parameterIndex + 2)

def isMacintoshArch():
  arch = currentArch()
  if not arch == 'x86_64':
    return False

  nsClassName = 'NSApplication'
  command = '(void*)objc_getClass("{}")'.format(nsClassName)

  return (fb.evaluateBooleanExpression(command + '!= nil'))

def isIOSSimulator():
  return fb.evaluateExpressionValue('(id)[[UIDevice currentDevice] model]').GetObjectDescription().lower().find('simulator') >= 0

def isIOSDevice():
  return not isMacintoshArch() and not isIOSSimulator()
