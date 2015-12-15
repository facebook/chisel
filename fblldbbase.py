#!/usr/bin/python

# Copyright (c) 2014, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

import lldb
import json

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

RET_MACRO = """
#define IS_JSON_OBJ(obj)\
    (obj != nil && ((bool)[NSJSONSerialization isValidJSONObject:obj] ||\
    (bool)[obj isKindOfClass:[NSString class]] ||\
    (bool)[obj isKindOfClass:[NSNumber class]]))
#define RET(ret) ({\
    if (!IS_JSON_OBJ(ret)) {\
        (void)[NSException raise:@"RET error" format:@"Invalied return type"];\
    }\
    NSDictionary *__dict = @{@"return":ret};\
    NSData *__data = (id)[NSJSONSerialization dataWithJSONObject:__dict options:0 error:NULL];\
    NSString *__str = (id)[[NSString alloc] initWithData:__data encoding:4];\
    (char *)[__str UTF8String];})
#define RETCString(ret)\
    ({NSString *___cstring_ret = [NSString stringWithUTF8String:ret];\
    RET(___cstring_ret);})
"""

def check_expr(expr):
    return expr.strip().split('\n')[-1].find('RET') != -1

# evaluates a batch of OC expression, the last expression must contain a RET marco
# and it will automatic transform the RET OC object to python object
# Example:
#       >>> fblldbbase.eval('NSString *str = @"hello world"; RET(@{@"key": str});')
#       {u'key': u'hello world'}
#
def eval(expr):
    if not check_expr(expr):
        raise Exception("expr not Invalied, the last expression should include a RET* marco")

    command = "({" + RET_MACRO + '\n' + expr + "})"
    ret = evaluateExpressionValue(command, True)
    if not ret.GetError().Success():
        raise Exception("eval expression error occur")
    else:
        process = lldb.debugger.GetSelectedTarget().GetProcess()
        error = lldb.SBError()
        ret = process.ReadCStringFromMemory(int(ret.GetValue(), 16), 256, error)
        if not error.Success():
            print error
            return None
        else:
            ret = json.loads(ret)
            return ret['return']
