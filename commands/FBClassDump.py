#!/usr/bin/python

import os
import re
import string

import lldb
import fblldbbase as fb
import fblldbobjcruntimehelpers as runtimeHelpers

def lldbcommands():
  return [
    FBPrintClassInstanceMethods(),
    FBPrintClassMethods()
  ]

class FBPrintClassInstanceMethods(fb.FBCommand):
  def name(self):
    return 'pclassinstancemethod'

  def description(self):
    return 'Print the class instance methods.'

  def args(self):
    return [ fb.FBCommandArgument(arg='class', type='Class', help='an OC Class.') ]

  def run(self, arguments, options):
    ocarray = instanceMethosOfClass(arguments[0])
    methodAddrs = covertOCArrayToPyArray(ocarray)

    methods = []
    for i in methodAddrs:
      method = createMethodFromOCMethod(i)
      if method is not None:
        methods.append(method)
        print "- " + method.prettyPrint()

class FBPrintClassMethods(fb.FBCommand):
  def name(self):
    return 'pclassmethod'

  def description(self):
    return 'Print the class`s class methods.'

  def args(self):
    return [ fb.FBCommandArgument(arg='class', type='Class', help='an OC Class.') ]

  def run(self, arguments, options):
    ocarray = instanceMethosOfClass(runtimeHelpers.object_getClass(arguments[0]))
    if not ocarray:
      print "-- have none method -- "
      return

    methodAddrs = covertOCArrayToPyArray(ocarray)

    methods = []
    for i in methodAddrs:
      method = createMethodFromOCMethod(i)
      if method is not None:
        methods.append(method)
        print "+ " + method.prettyPrint()

# I find that a method that has variable parameter can not b.evaluateExpression
# so I use numberWithLongLong: rather than -[NSString stringWithFormat:]
def instanceMethosOfClass(klass):
  tmpString = """
    unsigned int outCount;
    void **methods = (void **)class_copyMethodList((Class)$cls, &outCount);
    NSMutableArray *result = [NSMutableArray array];
    for (int i = 0; i < outCount; i++) {
      NSNumber *num = (NSNumber *)[NSNumber numberWithLongLong:(long long)methods[i]];
      [result addObject:num];
    }
    (void)free(methods);
    id ret = result.count ? [result copy] : nil;
    ret;
  """

  command = string.Template(tmpString).substitute(cls=klass)
  command = '({' + command + '})'
  ret = fb.evaluateExpression(command)
  if int(ret, 16) == 0: # return nil
    ret = None
  return ret

# OC array only can hold id, 
# @return an array whose instance type is str of the oc object`s address

def covertOCArrayToPyArray(oc_array):
  is_array = fb.evaluateBooleanExpression("[{} isKindOfClass:[NSArray class]]".format(oc_array))
  if not is_array:
    return None

  result = []
  count = fb.evaluateExpression("(int)[{} count]".format(oc_array))

  for i in range(int(count)):
    value = fb.evaluateExpression("(id)[{} objectAtIndex:{}]".format(oc_array, i))
    value = fb.evaluateExpression("(long long)[{} longLongValue]".format(value))
    result.append(value)

  return result


class Method:

  encodeMap = {
    'c': 'char',
    'i': 'int',
    's': 'short',
    'l': 'long',
    'q': 'long long',

    'C': 'unsigned char',
    'I': 'unsigned int',
    'S': 'unsigned short',
    'L': 'unsigned long',
    'Q': 'unsigned long long',

    'f': 'float',
    'd': 'double',
    'B': 'bool',
    'v': 'void',
    '*': 'char *',
    '@': 'id',
    '#': 'Class',
    ':': 'SEL',
  }

  def __init__(self, name, type_encoding, imp, oc_method):
    self.name = name
    self.type = type_encoding
    self.imp = imp
    self.oc_method = self.toHex(oc_method)

  def prettyPrint(self):
    # mast be bigger then 2, 0-idx for self, 1-st for SEL
    argnum = fb.evaluateIntegerExpression("method_getNumberOfArguments({})".format(self.oc_method))
    names = self.name.split(':')

    for i in range(2, argnum):
      arg_type = fb.evaluateCStringExpression("(char *)method_copyArgumentType({}, {})".format(self.oc_method, i))
      names[i-2] = names[i-2] + ":(" +  self.decode(arg_type) + ")arg" + str(i-2)

    string = " ".join(names)

    ret_type = fb.evaluateCStringExpression("(char *)method_copyReturnType({})".format(self.oc_method))
    return "({}){}".format(self.decode(ret_type), string)


  def decode(self, type):
    ret = type
    if type in Method.encodeMap:
      ret = Method.encodeMap[type]
    return ret

  def toHex(self, addr):
    return addr

  def __str__(self):
    return "<Method:" + self.oc_method + "> " + self.name + " --- " + self.type + " --- " + self.imp 

def createMethodFromOCMethod(method):
  process = lldb.debugger.GetSelectedTarget().GetProcess()
  error = lldb.SBError()

  nameValue = fb.evaluateExpression("(char *)method_getName({})".format(method))
  name = process.ReadCStringFromMemory(int(nameValue, 16), 256, error)

  if not error.Success():
    print "--error--"
    return None

  typeEncodingValue = fb.evaluateExpression("(char *)method_getTypeEncoding({})".format(method))
  type_encoding = process.ReadCStringFromMemory(int(typeEncodingValue, 16), 256, error)

  if not error.Success():
    print "--error--"
    return None

  imp = fb.evaluateExpression("(void *)method_getImplementation({})".format(method))
  return Method(name, type_encoding, imp, method)
