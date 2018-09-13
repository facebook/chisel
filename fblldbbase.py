#!/usr/bin/python

# Copyright (c) 2014, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

import lldb
import json
import shlex

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

  def lex(self, commandLine):
    return shlex.split(commandLine)

  def run(self, arguments, option):
    pass

def isSuccess(error):
  # When evaluating a `void` expression, the returned value will indicate an
  # error. This error is named: kNoResult. This error value does *not* mean
  # there was a problem. This logic follows what the builtin `expression`
  # command does. See: https://git.io/vwpjl (UserExpression.h)
  kNoResult = 0x1001
  return error.success or error.value == kNoResult

def importModule(frame, module):
  options = lldb.SBExpressionOptions()
  options.SetLanguage(lldb.eLanguageTypeObjC)
  value = frame.EvaluateExpression('@import ' + module, options)
  return isSuccess(value.error)

# evaluates expression in Objective-C++ context, so it will work even for
# Swift projects
def evaluateExpressionValue(expression, printErrors=True, language=lldb.eLanguageTypeObjC_plus_plus, tryAllThreads=False):
  frame = lldb.debugger.GetSelectedTarget().GetProcess().GetSelectedThread().GetSelectedFrame()
  options = lldb.SBExpressionOptions()
  options.SetLanguage(language)

  # Allow evaluation that contains a @throw/@catch.
  #   By default, ObjC @throw will cause evaluation to be aborted. At the time
  #   of a @throw, it's not known if the exception will be handled by a @catch.
  #   An exception that's caught, should not cause evaluation to fail.
  options.SetTrapExceptions(False)

  # Give evaluation more time.
  options.SetTimeoutInMicroSeconds(5000000) # 5s

  # Most Chisel commands are not multithreaded.
  options.SetTryAllThreads(tryAllThreads)

  value = frame.EvaluateExpression(expression, options)
  error = value.GetError()

  # Retry if the error could be resolved by first importing UIKit.
  if (error.type == lldb.eErrorTypeExpression and
      error.value == lldb.eExpressionParseError and
      importModule(frame, 'UIKit')):
    value = frame.EvaluateExpression(expression, options)
    error = value.GetError()

  if printErrors and not isSuccess(error):
    print error

  return value

def evaluateInputExpression(expression, printErrors=True):
  # HACK
  if expression.startswith('(id)'):
    return evaluateExpressionValue(expression, printErrors=printErrors).GetValue()

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
  return int(output, 0)

def evaluateBooleanExpression(expression, printErrors=True):
  return (int(evaluateIntegerExpression('(BOOL)(' + expression + ')', printErrors)) != 0)

def evaluateExpression(expression, printErrors=True):
  return evaluateExpressionValue(expression, printErrors=printErrors).GetValue()

def describeObject(expression, printErrors=True):
  return evaluateExpressionValue('(id)(' + expression + ')', printErrors).GetObjectDescription()

def evaluateEffect(expression, printErrors=True):
  evaluateExpressionValue('(void)(' + expression + ')', printErrors=printErrors)

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

#define RETURN_JSON(ret) ({\
    if (!IS_JSON_OBJ(ret)) {\
        (void)[NSException raise:@"Invalid RETURN argument" format:@""];\
    }\
    NSDictionary *__dict = @{(id)@"return":ret};\
    NSData *__data = (id)[NSJSONSerialization dataWithJSONObject:__dict options:0 error:NULL];\
    NSString *__str = (id)[[NSString alloc] initWithData:__data encoding:4];\
    (char *)[__str UTF8String];})

#define RETURN(ret) ret
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
  ret = evaluateExpressionValue(command, printErrors=True)
  if not ret.GetError().Success():
    print ret.GetError()
    return None

  isJson = expr.strip().split(';')[-2].find('RETURN_JSON') != -1
  if not isJson:
    return ret.GetValue()

  process = lldb.debugger.GetSelectedTarget().GetProcess()
  error = lldb.SBError()
  ret = process.ReadCStringFromMemory(int(ret.GetValue(), 16), 2**20, error)
  if not error.Success():
    print error
    return None
  else:
    ret = json.loads(ret)
    return ret['return']

def currentLanguage():
  return lldb.debugger.GetSelectedTarget().GetProcess().GetSelectedThread().GetSelectedFrame().GetCompileUnit().GetLanguage()
