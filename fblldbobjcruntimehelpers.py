#!/usr/bin/python

# Copyright (c) 2014, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

import lldb
import fblldbbase as fb
import re

def objc_getClass(className):
  command = '(void*)objc_getClass("{}")'.format(className)
  value = fb.evaluateExpression(command)
  return value

def object_getClass(object):
  command = '(void*)object_getClass({})'.format(object)
  value = fb.evaluateExpression(command)
  return value

def class_getName(klass):
  command = '(const char*)class_getName({})'.format(klass)
  value = fb.evaluateExpressionValue(command).GetSummary().strip('"')
  return value

def class_getSuperclass(klass):
  command = '(void*)class_getSuperclass({})'.format(klass)
  value = fb.evaluateExpression(command)
  return value

def class_getInstanceMethod(klass, selector):
  command = '(void*)class_getInstanceMethod({}, @selector({}))'.format(klass, selector)
  value = fb.evaluateExpression(command)
  return value

def currentArch():
  targetTriple = lldb.debugger.GetSelectedTarget().GetTriple()
  arch = targetTriple.split('-')[0]
  return arch

def functionPreambleExpressionForSelf():
  arch = currentArch()
  expressionForSelf = None
  if arch == 'i386':
    expressionForSelf = '*(id*)($esp+4)'
  elif arch == 'x86_64':
    expressionForSelf = '(id)$rdi'
  elif arch == 'arm64':
    expressionForSelf = '(id)$x0'
  elif re.match(r'^armv.*$', arch):
    expressionForSelf = '(id)$r0'
  return expressionForSelf

def functionPreambleExpressionForObjectParameterAtIndex(parameterIndex):
  arch = currentArch()
  expresssion = None
  if arch == 'i386':
    expresssion = '*(id*)($esp + ' + str(12 + parameterIndex * 4) + ')'
  elif arch == 'x86_64':
    if (parameterIndex > 3):
      raise Exception("Current implementation can not return object at index greater than 3 for arc x86_64")
    registersList = ['rdx', 'rcx', 'r8', 'r9']
    expresssion = '(id)$' + registersList[parameterIndex]
  elif arch == 'arm64':
    if (parameterIndex > 5):
      raise Exception("Current implementation can not return object at index greater than 5 for arm64")  
    expresssion = '(id)$x' + str(parameterIndex + 2)
  elif re.match(r'^armv.*$', arch):
    if (parameterIndex > 3):
      raise Exception("Current implementation can not return object at index greater than 1 for arm32")
    expresssion = '(id)$r' + str(parameterIndex + 2)
  return expresssion
