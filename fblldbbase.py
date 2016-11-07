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

# evaluates expression in Objective-C++ context, so it will work even for
# Swift projects
def evaluateExpressionValue(expression, printErrors=True):
  frame = lldb.debugger.GetSelectedTarget().GetProcess().GetSelectedThread().GetSelectedFrame()
  options = lldb.SBExpressionOptions()
  options.SetLanguage(lldb.eLanguageTypeObjC_plus_plus)
  options.SetTrapExceptions(False)
  value = frame.EvaluateExpression(expression, options)
  error = value.GetError()

  if printErrors and error.Fail():
    # When evaluating a `void` expression, the returned value has an error code named kNoResult.
    # This is not an error that should be printed. This follows what the built in `expression` command does.
    # See: https://git.io/vwpjl (UserExpression.h)
    kNoResult = 0x1001
    if error.GetError() != kNoResult:
      print error

  return value

def evaluateInputExpression(expression, printErrors=True):
  # HACK
  if expression.startswith('(id)'):
    return evaluateExpressionValue(expression, printErrors).GetValue()

  frame = lldb.debugger.GetSelectedTarget().GetProcess().GetSelectedThread().GetSelectedFrame()
  options = lldb.SBExpressionOptions()
  options.SetTrapExceptions(False)
  value = frame.EvaluateExpression(expression, options)
  error = value.GetError()

  if printErrors and error.Fail():
    print error

  return value.GetValue()

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

def describeObject(expression, printErrors=True):
  return evaluateExpressionValue('(id)(' + expression + ')', printErrors).GetObjectDescription()

def evaluateEffect(expression, printErrors=True):
  evaluateExpressionValue('(void)(' + expression + ')', printErrors)

def evaluateObjectExpression(expression, printErrors=True):
  return evaluateExpression('(id)(' + expression + ')', printErrors)

def evaluateCStringExpression(expression, printErrors=True):
  ret = evaluateExpression(expression, printErrors)

  process = lldb.debugger.GetSelectedTarget().GetProcess()
  error = lldb.SBError()
  ret = process.ReadCStringFromMemory(int(ret, 16), 256, error)
  if error.Success():
    return ret
  else:
    if printErrors:
      print error
    return None


RETURN_MACRO = """
#define IS_JSON_OBJ(obj)\
    (obj != nil && ((bool)[NSJSONSerialization isValidJSONObject:obj] ||\
    (bool)[obj isKindOfClass:[NSString class]] ||\
    (bool)[obj isKindOfClass:[NSNumber class]]))
#define RETURN(ret) ({\
    if (!IS_JSON_OBJ(ret)) {\
        (void)[NSException raise:@"Invalid RETURN argument" format:@""];\
    }\
    NSDictionary *__dict = @{@"return":ret};\
    NSData *__data = (id)[NSJSONSerialization dataWithJSONObject:__dict options:0 error:NULL];\
    NSString *__str = (id)[[NSString alloc] initWithData:__data encoding:4];\
    (char *)[__str UTF8String];})
#define RETURNCString(ret)\
    ({NSString *___cstring_ret = [NSString stringWithUTF8String:ret];\
    RETURN(___cstring_ret);})
"""

def check_expr(expr):
  return expr.strip().split(';')[-2].find('RETURN') != -1

# evaluate a batch of Objective-C expressions, the last expression must contain a RETURN marco
# and it will automatic transform the Objective-C object to Python object
# Example:
#       >>> fblldbbase.evaluate('NSString *str = @"hello world"; RETURN(@{@"key": str});')
#       {u'key': u'hello world'}
def evaluate(expr):
  if not check_expr(expr):
    raise Exception("Invalid Expression, the last expression not include a RETURN family marco")

  command = "({" + RETURN_MACRO + '\n' + expr + "})"
  ret = evaluateExpressionValue(command, True)
  if not ret.GetError().Success():
    print ret.GetError()
    return None
  else:
    process = lldb.debugger.GetSelectedTarget().GetProcess()
    error = lldb.SBError()
    ret = process.ReadCStringFromMemory(int(ret.GetValue(), 16), 2**20, error)
    if not error.Success():
      print error
      return None
    else:
      ret = json.loads(ret)
      return ret['return']
