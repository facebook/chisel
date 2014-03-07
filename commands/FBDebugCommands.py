#!/usr/bin/python

import lldb
import fblldbbase as fb
import fblldbobjcruntimehelpers as objc

import re

def lldbcommands():
  return [
    FBWatchInstanceVariableCommand(),
    FBMethodBreakpointCommand(),
  ]

class FBWatchInstanceVariableCommand(fb.FBCommand):
  def name(self):
    return 'wivar'

  def description(self):
    return "Set a watchpoint for an object's instance variable."

  def args(self):
    return [
      fb.FBCommandArgument(arg='object', type='id', help='Object expression to be evaluated.'),
      fb.FBCommandArgument(arg='ivarName', help='Name of the instance variable to watch.')
    ]

  def run(self, arguments, options):
    commandForObject, ivarName = arguments

    objectAddress = int(fb.evaluateObjectExpression(commandForObject), 0)

    ivarOffsetCommand = '(ptrdiff_t)ivar_getOffset((void *)object_getInstanceVariable((id){}, "{}", 0))'.format(objectAddress, ivarName)
    ivarOffset = fb.evaluateIntegerExpression(ivarOffsetCommand)

    # A multi-statement command allows for variables scoped to the command, not permanent in the session like $variables.
    ivarSizeCommand = ('unsigned int size = 0;'
                       'char *typeEncoding = (char *)ivar_getTypeEncoding((void *)class_getInstanceVariable((Class)object_getClass((id){}), "{}"));'
                       '(char *)NSGetSizeAndAlignment(typeEncoding, &size, 0);'
                       'size').format(objectAddress, ivarName)
    ivarSize = int(fb.evaluateExpression(ivarSizeCommand), 0)

    error = lldb.SBError()
    watchpoint = lldb.debugger.GetSelectedTarget().WatchAddress(objectAddress + ivarOffset, ivarSize, False, True, error)

    if error.Success():
      print 'Remember to delete the watchpoint using: watchpoint delete {}'.format(watchpoint.GetID())
    else:
      print 'Could not create the watchpoint: {}'.format(error.GetCString())

class FBMethodBreakpointCommand(fb.FBCommand):
  def name(self):
    return 'bmessage'

  def description(self):
    return "Set a breakpoint for a selector on a class, even if the class itself doesn't override that selector. It walks the hierarchy until it finds a class that does implement the selector and sets a conditional breakpoint there."

  def args(self):
    return [
      fb.FBCommandArgument(arg='expression', type='string', help='Expression to set a breakpoint on, e.g. "-[MyView setFrame:]", "+[MyView awesomeClassMethod]" or "-[0xabcd1234 setFrame:]"'),
    ]

  def run(self, arguments, options):
    expression = arguments[0]

    match = re.match(r'([-+])*\[(.*) (.*)\]', expression)

    if not match:
      print 'Failed to parse expression. Do you even Objective-C?!'
      return

    expressionForSelf = objc.functionPreambleExpressionForSelf()
    if not expressionForSelf:
      print 'Your architecture, {}, is truly fantastic. However, I don\'t currently support it.'.format(arch)
      return

    methodTypeCharacter = match.group(1)
    classNameOrExpression = match.group(2)
    selector = match.group(3)

    methodIsClassMethod = (methodTypeCharacter == '+')

    if not methodIsClassMethod:
      # The default is instance method, and methodTypeCharacter may not actually be '-'.
      methodTypeCharacter = '-'

    targetIsClass = False
    targetObject = fb.evaluateObjectExpression('({})'.format(classNameOrExpression), False)

    if not targetObject:
      # If the expression didn't yield anything then it's likely a class. Assume it is.
      # We will check again that the class does actually exist anyway.
      targetIsClass = True
      targetObject = fb.evaluateObjectExpression('[{} class]'.format(classNameOrExpression), False)

    targetClass = fb.evaluateObjectExpression('[{} class]'.format(targetObject), False)

    if not targetClass or int(targetClass, 0) == 0:
      print 'Couldn\'t find a class from the expression "{}". Did you typo?'.format(classNameOrExpression)
      return

    if methodIsClassMethod:
      targetClass = objc.object_getClass(targetClass)

    found = False
    nextClass = targetClass

    while not found and int(nextClass, 0) > 0:
      if classItselfImplementsSelector(nextClass, selector):
        found = True
      else:
        nextClass = objc.class_getSuperclass(nextClass)

    if not found:
      print 'There doesn\'t seem to be an implementation of {} in the class hierarchy. Made a boo boo with the selector name?'.format(selector)
      return

    breakpointClassName = objc.class_getName(nextClass)
    breakpointFullName = '{}[{} {}]'.format(methodTypeCharacter, breakpointClassName, selector)

    breakpointCondition = None
    if targetIsClass:
      breakpointCondition = '(void*)object_getClass({}) == {}'.format(expressionForSelf, targetClass)
    else:
      breakpointCondition = '(void*){} == {}'.format(expressionForSelf, targetObject)

    print 'Setting a breakpoint at {} with condition {}'.format(breakpointFullName, breakpointCondition)

    lldb.debugger.HandleCommand('breakpoint set --fullname "{}" --condition "{}"'.format(breakpointFullName, breakpointCondition))

def classItselfImplementsSelector(klass, selector):
  thisMethod = objc.class_getInstanceMethod(klass, selector)
  if thisMethod == 0:
    return False

  superklass = objc.class_getSuperclass(klass)
  superMethod = objc.class_getInstanceMethod(superklass, selector)
  if thisMethod == superMethod:
    return False
  else:
    return True
