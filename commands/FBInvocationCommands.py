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

def lldbcommands():
  return [
    FBPrintInvocation(),
  ]

class FBPrintInvocation(fb.FBCommand):
  def name(self):
    return 'pinvocation'

  def description(self):
    return 'Print the stack frame, receiver, and arguments of the current invocation. It will fail to print all arguments if any arguments are variadic (varargs).\n\nNOTE: Sadly this is currently only implemented on x86.'

  def options(self):
    return [
            fb.FBCommandArgument(short='-a', long='--all', arg='all', default=False, boolean=True, help='Specify to print the entire stack instead of just the current frame.'),
            ]

  def run(self, arguments, options):
    target = lldb.debugger.GetSelectedTarget()

    if not re.match(r'.*i386.*', target.GetTriple()):
      print 'Only x86 is currently supported (32-bit iOS Simulator or Mac OS X).'
      return

    thread = target.GetProcess().GetSelectedThread()

    if options.all:
      for frame in thread:
        printInvocationForFrame(frame)
        print '---------------------------------'
    else:
      frame = thread.GetSelectedFrame()
      printInvocationForFrame(frame)

def printInvocationForFrame(frame):
  print frame

  symbolName = frame.GetSymbol().GetName()
  if not re.match(r'[-+]\s*\[.*\]', symbolName):
    return

  self = findArgAtIndexFromStackFrame(frame, 0)
  cmd = findArgAtIndexFromStackFrame(frame, 1)

  commandForSignature = '[(id)' + self + ' methodSignatureForSelector:(char *)sel_getName(' + cmd + ')]'
  signatureValue = fb.evaluateExpressionValue('(id)' + commandForSignature)

  if signatureValue.GetError() is not None and str(signatureValue.GetError()) != 'success':
    print "My sincerest apologies. I couldn't find a method signature for the selector."
    return

  signature = signatureValue.GetValue()

  arg0 = stackStartAddressInSelectedFrame(frame)
  commandForInvocation = '[NSInvocation _invocationWithMethodSignature:(id)' + signature + ' frame:((void *)' + str(arg0) + ')]'
  invocation = fb.evaluateExpression('(id)' + commandForInvocation)

  if invocation:
    prettyPrintInvocation(frame, invocation)
  else:
    print frame

def stackStartAddressInSelectedFrame(frame):
  # Determine if the %ebp register has already had the stack register pushed into it (always the first instruction)
  frameSymbol = frame.GetSymbolContext(0).GetSymbol()
  frameStartAddress = frameSymbol.GetStartAddress().GetLoadAddress(lldb.debugger.GetSelectedTarget())

  currentPC = frame.GetPC()

  offset = currentPC - frameStartAddress

  if offset == 0:
    return int(frame.EvaluateExpression('($esp + 4)').GetValue())
  elif offset == 1:
    return int(frame.EvaluateExpression('($esp + 8)').GetValue())
  else:
    return int(frame.EvaluateExpression('($ebp + 8)').GetValue())
    

def findArgAtIndexFromStackFrame(frame, index):
  return fb.evaluateExpression('*(int *)' + str(findArgAdressAtIndexFromStackFrame(frame, index)))

def findArgAdressAtIndexFromStackFrame(frame, index):
  arg0 = stackStartAddressInSelectedFrame(frame)
  arg = arg0 + 4 * index
  return arg

def prettyPrintInvocation(frame, invocation):
  object = fb.evaluateExpression('(id)[(id)' + invocation + ' target]')
  selector = fb.evaluateExpressionValue('(char *)sel_getName((SEL)[(id)' + invocation + ' selector])').GetSummary()
  selector = re.sub(r'^"|"$', '', selector)

  objectClassValue = fb.evaluateExpressionValue('(id)object_getClass((id)' + object + ')')
  objectClass = objectClassValue.GetObjectDescription()

  description = fb.evaluateExpressionValue('(id)' + invocation).GetObjectDescription()
  argDescriptions = description.splitlines(True)[4:]

  print 'NSInvocation: ' + invocation
  print 'self: ' + fb.evaluateExpression('(id)' + object)

  if len(argDescriptions) > 0:
    print '\n' + str(len(argDescriptions)) + ' Arguments:' if len(argDescriptions) > 1 else '\nArgument:'

    index = 2
    for argDescription in argDescriptions:
      s = re.sub(r'argument [0-9]+: ', '', argDescription)

      lldb.debugger.HandleCommand('expr void *$v')
      lldb.debugger.HandleCommand('expr (void)[' + invocation + ' getArgument:&$v atIndex:' + str(index) + ']')

      address = findArgAdressAtIndexFromStackFrame(frame, index)

      encoding = s.split(' ')[0]
      description = ' '.join(s.split(' ')[1:])

      readableString = argumentAsString(frame, address, encoding)

      if readableString:
        print readableString
      else:
        if encoding[0] == '{':
          encoding = encoding[1:len(encoding)-1]
        print (hex(address) + ', address of ' + encoding + ' ' + description).strip()

      index += 1

def argumentAsString(frame, address, encoding):
  if encoding[0] == '{':
    encoding = encoding[1:len(encoding)-1]

  encodingMap = {
    'c' : 'char',
    'i' : 'int',
    's' : 'short',
    'l' : 'long',
    'q' : 'long long',

    'C' : 'unsigned char',
    'I' : 'unsigned int',
    'S' : 'unsigned short',
    'L' : 'unsigned long',
    'Q' : 'unsigned long long',

    'f' : 'float',
    'd' : 'double',
    'B' : 'bool',
    'v' : 'void',
    '*' : 'char *',
    '@' : 'id',
    '#' : 'Class',
    ':' : 'SEL',
  }

  pointers = ''
  while encoding[0] == '^':
    pointers += '*'
    encoding = encoding[1:]

  type = None
  if encoding in encodingMap:
    type = encodingMap[encoding]

  if type and pointers:
    type = type + ' ' + pointers

  if not type:
    # Handle simple structs: {CGPoint=ff}, {CGSize=ff}, {CGRect={CGPoint=ff}{CGSize=ff}}
    if encoding[0] == '{':
      encoding = encoding[1:]

    type = re.sub(r'=.*', '', encoding)
    if pointers:
      type += ' ' + pointers

  if type:
    value = frame.EvaluateExpression('*(' + type + ' *)' + str(address))

    if value.GetError() is None or str(value.GetError()) == 'success':
      description = None

      if encoding == '@':
        description = value.GetObjectDescription()

      if not description:
        description = value.GetValue()
      if not description:
        description = value.GetSummary()
      if description:
        return type + ': ' + description
  
  return None
