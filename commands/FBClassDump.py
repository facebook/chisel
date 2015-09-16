#!/usr/bin/python

# Copyright (c) 2014, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

import os
import re
import string

import lldb
import fblldbbase as fb
import fblldbobjcruntimehelpers as runtimeHelpers

def lldbcommands():
  return [
    FBPrintClassInstanceMethods()
  ]

class FBPrintClassInstanceMethods(fb.FBCommand):
  def name(self):
    return 'pci'

  def description(self):
    return 'Print the class instance methods.'

  def args(self):
    return [ fb.FBCommandArgument(arg='class', type='Class', help='an OC Class.') ]

  def run(self, arguments, options):
    ocarray = instanceMethosOfClass(arguments[0])
    methodAddrs = covertOCArrayToPyArray(ocarray)
    methods = createMethodsFromPointers(methodAddrs)
    print methods

def instanceMethosOfClass(klass):
  tmpString = """
    unsigned int outCount;
    void **methods = (void **)class_copyMethodList([self class], &outCount);
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

  return fb.evaluateExpression(command)

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
    value = fb.evaluateExpression("(id)[{} longLongValue]".format(value))
    result.append(value)

  return result


class Method:
  def __init__(self, name, type_encoding, imp):
    self.name = name
    self.type = type_encoding
    self.imp = imp

def createMethodsFromPointers(pointers):
  methods = []
  for p in pointers:
    nameValue = fb.evaluateExpression("(char *)method_getName({})".format(p))

    process = lldb.debugger.GetSelectedTarget().GetProcess()
    error = lldb.SBError()

    name = process.ReadCStringFromMemory(int(nameValue, 16), 256, error)

    if not error.Success():
      print "--debug--"
      continue

    typeEncodingValue = fb.evaluateExpression("(char *)method_getTypeEncoding({})".format(p))
    type_encoding = process.ReadCStringFromMemory(int(typeEncodingValue, 16), 256, error)

    if not error.Success():
      print "--debug--"
      continue

    imp = fb.evaluateExpression("(void *)method_getImplementation({})".format(p))

    print name, type_encoding, imp
    methods.append(Method(name, type_encoding, imp));

  return methods
