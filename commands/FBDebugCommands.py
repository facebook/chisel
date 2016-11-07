#!/usr/bin/python

import lldb
import fblldbbase as fb
import fblldbobjcruntimehelpers as objc

import re

def lldbcommands():
  return [
    FBWatchInstanceVariableCommand(),
    FBFrameworkAddressBreakpointCommand(),
    FBMethodBreakpointCommand(),
    FBMemoryWarningCommand(),
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

    ivarOffsetCommand = '(ptrdiff_t)ivar_getOffset((void*)object_getInstanceVariable((id){}, "{}", 0))'.format(objectAddress, ivarName)
    ivarOffset = int(fb.evaluateExpression(ivarOffsetCommand), 0)

    # A multi-statement command allows for variables scoped to the command, not permanent in the session like $variables.
    ivarSizeCommand = ('unsigned int size = 0;'
                       'char *typeEncoding = (char *)ivar_getTypeEncoding((void*)class_getInstanceVariable((Class)object_getClass((id){}), "{}"));'
                       '(char *)NSGetSizeAndAlignment(typeEncoding, &size, 0);'
                       'size').format(objectAddress, ivarName)
    ivarSize = int(fb.evaluateExpression(ivarSizeCommand), 0)

    error = lldb.SBError()
    watchpoint = lldb.debugger.GetSelectedTarget().WatchAddress(objectAddress + ivarOffset, ivarSize, False, True, error)

    if error.Success():
      print 'Remember to delete the watchpoint using: watchpoint delete {}'.format(watchpoint.GetID())
    else:
      print 'Could not create the watchpoint: {}'.format(error.GetCString())

class FBFrameworkAddressBreakpointCommand(fb.FBCommand):
  def name(self):
    return 'binside'

  def description(self):
    return "Set a breakpoint for a relative address within the framework/library that's currently running. This does the work of finding the offset for the framework/library and sliding your address accordingly."

  def args(self):
    return [
      fb.FBCommandArgument(arg='address', type='string', help='Address within the currently running framework to set a breakpoint on.'),
    ]

  def run(self, arguments, options):
    library_address = int(arguments[0], 0)
    address = int(lldb.debugger.GetSelectedTarget().GetProcess().GetSelectedThread().GetSelectedFrame().GetModule().ResolveFileAddress(library_address))

    lldb.debugger.HandleCommand('breakpoint set --address {}'.format(address))

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

    methodPattern = re.compile(r"""
      (?P<scope>[-+])?
      \[
        (?P<target>.*?)
        (?P<category>\(.+\))?
        \s+
        (?P<selector>.*)
      \]
""", re.VERBOSE)

    match = methodPattern.match(expression)

    if not match:
      print 'Failed to parse expression. Do you even Objective-C?!'
      return

    expressionForSelf = objc.functionPreambleExpressionForSelf()
    if not expressionForSelf:
      print 'Your architecture, {}, is truly fantastic. However, I don\'t currently support it.'.format(arch)
      return

    methodTypeCharacter = match.group('scope')
    classNameOrExpression = match.group('target')
    category = match.group('category')
    selector = match.group('selector')

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
    formattedCategory = category if category else ''
    breakpointFullName = '{}[{}{} {}]'.format(methodTypeCharacter, breakpointClassName, formattedCategory, selector)

    if targetIsClass:
      breakpointCondition = '(void*)object_getClass({}) == {}'.format(expressionForSelf, targetClass)
    else:
      breakpointCondition = '(void*){} == {}'.format(expressionForSelf, targetObject)

    print 'Setting a breakpoint at {} with condition {}'.format(breakpointFullName, breakpointCondition)

    if category:
      lldb.debugger.HandleCommand('breakpoint set --skip-prologue false --fullname "{}" --condition "{}"'.format(breakpointFullName, breakpointCondition))
    else:
      breakpointPattern = '{}\[{}(\(.+\))? {}\]'.format(methodTypeCharacter, breakpointClassName, selector)
      lldb.debugger.HandleCommand('breakpoint set --skip-prologue false --func-regex "{}" --condition "{}"'.format(breakpointPattern, breakpointCondition))

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

class FBMemoryWarningCommand(fb.FBCommand):
  def name(self):
    return 'mwarning'

  def description(self):
    return 'simulate a memory warning'

  def run(self, arguments, options):
    fb.evaluateEffect('[[UIApplication sharedApplication] performSelector:@selector(_performMemoryWarning)]')
