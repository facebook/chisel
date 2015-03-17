#!/usr/bin/python

# Copyright (c) 2014, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

import lldb

class FBCommandArgument:
  def __init__(self, short='', long='', arg='', type='', help='', default='', boolean=False):
    self.shortName = short
    self.longName = long
    self.argName = arg
    self.argType = type
    self.help = help
    self.default = default
    self.boolean = boolean

class FBCommand:
  def name(self):
    return None

  def options(self):
    return []

  def args(self):
    return []

  def description(self):
    return ''

  def run(self, arguments, option):
    pass


def evaluateExpressionValueWithLanguage(expression, language, printErrors):
  # lldb.frame is supposed to contain the right frame, but it doesnt :/ so do the dance
  frame = lldb.debugger.GetSelectedTarget().GetProcess().GetSelectedThread().GetSelectedFrame()
  expr_options = lldb.SBExpressionOptions()
  expr_options.SetLanguage(language)  # requires lldb r210874 (2014-06-13) / Xcode 6
  value = frame.EvaluateExpression(expression, expr_options)
  if printErrors and value.GetError() is not None and str(value.GetError()) != 'success':
    print value.GetError()
  return value

def evaluateExpressionValueInFrameLanguage(expression, printErrors=True):
  # lldb.frame is supposed to contain the right frame, but it doesnt :/ so do the dance
  frame = lldb.debugger.GetSelectedTarget().GetProcess().GetSelectedThread().GetSelectedFrame()
  language = frame.GetCompileUnit().GetLanguage()  # requires lldb r222189 (2014-11-17)
  return evaluateExpressionValueWithLanguage(expression, language, printErrors)

# evaluates expression in Objective-C++ context, so it will work even for
# Swift projects
def evaluateExpressionValue(expression, printErrors=True):
  return evaluateExpressionValueWithLanguage(expression, lldb.eLanguageTypeObjC_plus_plus, printErrors)

def evaluateIntegerExpression(expression, printErrors=True):
  output = evaluateExpression('(int)(' + expression + ')', printErrors).replace('\'', '')
  if output.startswith('\\x'): # Booleans may display as \x01 (Hex)
    output = output[2:]
  elif output.startswith('\\'): # Or as \0 (Dec)
    output = output[1:]
  return int(output, 16)

def evaluateBooleanExpression(expression, printErrors=True):
  return (int(evaluateIntegerExpression('(BOOL)(' + expression + ')', printErrors)) != 0)

def evaluateExpression(expression, printErrors=True):
  return evaluateExpressionValue(expression, printErrors).GetValue()

def evaluateObjectExpression(expression, printErrors=True):
  return evaluateExpression('(id)(' + expression + ')', printErrors)
