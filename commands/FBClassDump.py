#!/usr/bin/python

import os
import re
import string

import lldb
import fblldbbase as fb
import fblldbobjcruntimehelpers as runtimeHelpers

def lldbcommands():
  return [
    FBPrintMethods()
  ]

class FBPrintMethods(fb.FBCommand):
  def name(self):
    return 'pmethods'

  def description(self):
    return 'Print the class instance methods.'

  def options(self):
    return [
      fb.FBCommandArgument(short='-a', long='--address', arg='showaddr', help='Print the implementation address of the method', default=False, boolean=True),
      fb.FBCommandArgument(short='-i', long='--instance', arg='insmethod', help='Print the instance methods', default=False, boolean=True),
      fb.FBCommandArgument(short='-c', long='--class', arg='clsmethod', help='Print the class methods', default=False, boolean=True)
    ]

  def args(self):
    return [ fb.FBCommandArgument(arg='class or instance', type='id or Class', help='an Objective-C Class.') ]

  def run(self, arguments, options):
    cls = arguments[0]
    if not isClassObject(cls):
        cls = runtimeHelpers.object_getClass(cls)
        if not isClassObject(cls):
            raise Exception('Invalid argument. Please specify an instance or a Class.')

    if options.clsmethod:
      print 'Class Methods:'
      printClassMethods(cls, options.showaddr)

    if options.insmethod:
      print '\nInstance Methods:'
      printInstanceMethods(cls, options.showaddr)

    if not options.clsmethod and not options.insmethod:
      print 'Class Methods:'
      printClassMethods(cls, options.showaddr)
      print '\nInstance Methods:'
      printInstanceMethods(cls, options.showaddr)

def isClassObject(arg):
    return runtimeHelpers.class_isMetaClass(runtimeHelpers.object_getClass(arg))

def printInstanceMethods(cls, showaddr=False, prefix='-'):
    ocarray = instanceMethodsOfClass(cls)
    if not ocarray:
      print "No instance methods were found."
      return

    methodAddrs = covertOCArrayToPyArray(ocarray)
    methods = []
    for i in methodAddrs:
      method = createMethodFromOCMethod(i)
      if method is not None:
        methods.append(method)
        if showaddr:
          print prefix + ' ' + method.prettyPrint() + ' ' + method.imp
        else:
          print prefix + ' ' + method.prettyPrint()


def printClassMethods(cls, showaddr=False):
    printInstanceMethods(runtimeHelpers.object_getClass(cls), showaddr, '+')

# Use numberWithLongLong: rather than -[NSString stringWithFormat:] 
# since evaluateExpression doesn't work with variable arguments.
def instanceMethodsOfClass(klass):
  tmpString = """
    unsigned int outCount;
    void **methods = (void **)class_copyMethodList((Class)$cls, &outCount);
    NSMutableArray *result = [NSMutableArray array];
    for (int i = 0; i < outCount; i++) {
      NSNumber *num = (NSNumber *)[NSNumber numberWithLongLong:(long long)methods[i]];
      [result addObject:num];
    }
    id ret = result.count ? [result copy] : nil;
    ret;
  """

  command = string.Template(tmpString).substitute(cls=klass)
  command = '({' + command + '})'
  ret = fb.evaluateExpressionValue(command)
  if not ret.GetError().Success():
    return None

  ret = ret.GetValue()
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
    argnum = fb.evaluateIntegerExpression("method_getNumberOfArguments({})".format(self.oc_method))
    names = self.name.split(':')

    # the argnum count must be bigger then 2, index 0 for self, index 1 for SEL
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
    print error
    return None

  typeEncodingValue = fb.evaluateExpression("(char *)method_getTypeEncoding({})".format(method))
  type_encoding = process.ReadCStringFromMemory(int(typeEncodingValue, 16), 256, error)

  if not error.Success():
    print error
    return None

  imp = fb.evaluateExpression("(void *)method_getImplementation({})".format(method))
  return Method(name, type_encoding, imp, method)
