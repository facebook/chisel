#!/usr/bin/python

import lldb
import fblldbbase as fb
import fblldbobjcruntimehelpers as objc

import sys
import os
import re
import string

def lldbcommands():
  return [
    FBWatchInstanceVariableCommand(),
    FBFrameworkAddressBreakpointCommand(),
    FBMethodBreakpointCommand(),
    FBMemoryWarningCommand(),
    FBFindInstancesCommand(),
    FBMethodBreakpointEnableCommand(),
    FBMethodBreakpointDisableCommand(),
    FBHeapFromCommand(),
    FBSequenceCommand(),
    FBEvaluateFile(),
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


def switchBreakpointState(expression,on):

  expression_pattern = re.compile(r'{}'.format(expression),re.I)

  target = lldb.debugger.GetSelectedTarget()
  for breakpoint in target.breakpoint_iter():
    if breakpoint.IsEnabled() != on and (expression_pattern.search(str(breakpoint))):
      print str(breakpoint)
      breakpoint.SetEnabled(on)      
    for location in breakpoint:
      if location.IsEnabled() != on and (expression_pattern.search(str(location)) or expression == hex(location.GetAddress()) ):
        print str(location)
        location.SetEnabled(on)

class FBMethodBreakpointEnableCommand(fb.FBCommand):
  def name(self):
    return 'benable'

  def description(self):
    return """
    Enable a set of breakpoints for a regular expression

    Examples:

          * benable ***address***
          benable 0x0000000104514dfc
          benable 0x183e23564

          #use `benable *filename*` to switch all breakpoints in this file to `enable`
          benable SUNNetService.m 

          #use `benable ***module(AppName)***` to switch all breakpoints in this module to `enable`
          benable UIKit
          benable Foundation 

    """

  def args(self):
    return [
      fb.FBCommandArgument(arg='expression', type='string', help='Expression to enable breakpoint'),
    ]

  def run(self, arguments, options):
    expression = arguments[0]
    switchBreakpointState(expression,True)

class FBMethodBreakpointDisableCommand(fb.FBCommand):
  def name(self):
    return 'bdisable'

  def description(self):
    return """
    Disable a set of breakpoints for a regular expression

    Examples:

          * bdisable ***address***
          bdisable 0x0000000104514dfc
          bdisable 0x183e23564

          #use `bdisable *filename*` to switch all breakpoints in this file to `disable`
          bdisable SUNNetService.m 

          #use `bdisable ***module(AppName)***` to switch all breakpoints in this module to `disable`
          bdisable UIKit
          bdisable Foundation 

    """
  def args(self):
    return [
      fb.FBCommandArgument(arg='expression', type='string', help='Expression to disable breakpoint'),
    ]

  def run(self, arguments, options):
    expression = arguments[0]
    switchBreakpointState(expression,False)

class FBFindInstancesCommand(fb.FBCommand):
  def name(self):
    return 'findinstances'

  def args(self):
    return [
      fb.FBCommandArgument(arg='type', help='Class or protocol name'),
      fb.FBCommandArgument(arg='query', default=' ', # space is a hack to mark optional
                           help='Query expression, uses NSPredicate syntax')
    ]

  def description(self):
    return """
    Find instances of specified ObjC classes.

    This command scans memory and uses heuristics to identify instances of
    Objective-C classes. This includes Swift classes that descend from NSObject.

    Basic examples:

        findinstances UIScrollView
        findinstances *UIScrollView
        findinstances UIScrollViewDelegate

    These basic searches find instances of the given class or protocol. By
    default, subclasses of the class or protocol are included in the results. To
    find exact class instances, add a `*` prefix, for example: *UIScrollView.

    Advanced examples:

        # Find views that are either: hidden, invisible, or not in a window
        findinstances UIView hidden == true || alpha == 0 || window == nil
        # Find views that have either a zero width or zero height
        findinstances UIView layer.bounds.#size.width == 0 || layer.bounds.#size.height == 0
        # Find leaf views that have no subviews
        findinstances UIView subviews.@count == 0
        # Find dictionaries that have keys that might be passwords or passphrases
        findinstances NSDictionary any @allKeys beginswith 'pass'

    These examples make use of a filter. The filter is implemented with
    NSPredicate, see its documentaiton for more details. Basic NSPredicate
    expressions have relatively predicatable syntax. There are some exceptions
    as seen above, see https://github.com/facebook/chisel/wiki/findinstances.
    """

  def lex(self, commandLine):
    # Can't use default shlex splitting because it strips quotes, which results
    # in invalid NSPredicate syntax. Split the input into type and rest (query).
    return commandLine.split(' ', 1)

  def run(self, arguments, options):
    if not self.loadChiselIfNecessary():
      return

    if len(arguments) == 0 or not arguments[0].strip():
      print 'Usage: findinstances <classOrProtocol> [<predicate>]; Run `help findinstances`'
      return

    query = arguments[0]
    predicate = arguments[1].strip()
    # Escape double quotes and backslashes.
    predicate = re.sub('([\\"])', r'\\\1', predicate)
    call = '(void)PrintInstances("{}", "{}")'.format(query, predicate)
    fb.evaluateExpressionValue(call)

  def loadChiselIfNecessary(self):
    target = lldb.debugger.GetSelectedTarget()
    symbol_contexts = target.FindSymbols('PrintInstances', lldb.eSymbolTypeCode)
    if any(ctx.symbol.IsValid() for ctx in symbol_contexts):
      return True

    path = self.chiselLibraryPath()
    if not os.path.exists(path):
      print 'Chisel library missing: ' + path
      return False

    module = fb.evaluateExpressionValue('(void*)dlopen("{}", 2)'.format(path))
    if module.unsigned != 0 or target.module['Chisel']:
      return True

    # `errno` is a macro that expands to a call to __error(). In development,
    # lldb was not getting a correct value for `errno`, so `__error()` is used.
    errno = fb.evaluateExpressionValue('*(int*)__error()').value
    error = fb.evaluateExpressionValue('(char*)dlerror()')
    if errno == 50:
      # KERN_CODESIGN_ERROR from <mach/kern_return.h>
      print 'Error loading Chisel: Code signing failure; Must re-run codesign'
    elif error.unsigned != 0:
      print 'Error loading Chisel: ' + error.summary
    elif errno != 0:
      error = fb.evaluateExpressionValue('(char*)strerror({})'.format(errno))
      if error.unsigned != 0:
        print 'Error loading Chisel: ' + error.summary
      else:
        print 'Error loading Chisel (errno {})'.format(errno)
    else:
      print 'Unknown error loading Chisel'

    return False

  def chiselLibraryPath(self):
    # script os.environ['CHISEL_LIBRARY_PATH'] = '/path/to/custom/Chisel'
    path = os.getenv('CHISEL_LIBRARY_PATH')
    if path and os.path.exists(path):
      return path

    source_path = sys.modules[__name__].__file__
    source_dir = os.path.dirname(source_path)
    # ugh: ../.. is to back out of commands/, then back out of libexec/
    return os.path.join(source_dir, '..', '..', 'lib', 'Chisel.framework', 'Chisel')


class FBHeapFromCommand(fb.FBCommand):
  def name(self):
    return 'heapfrom'

  def description(self):
    return 'Show all nested heap pointers contained within a given variable.'

  def run(self, arguments, options):
    # This command is like `expression --synthetic-type false`, except only showing nested heap references.
    var = self.context.frame.var(arguments[0])
    if not var or not var.IsValid():
      self.result.SetError('No variable named "{}"'.format(arguments[0]))
      return

    # Use the actual underlying structure of the variable, not the human friendly (synthetic) one.
    root = var.GetNonSyntheticValue()

    # Traversal of SBValue tree to get leaf nodes, which is where heap pointers will be.
    leafs = []
    queue = [root]
    while queue:
        node = queue.pop(0)
        if node.num_children == 0:
            leafs.append(node)
        else:
            queue += [node.GetChildAtIndex(i) for i in range(node.num_children)]

    pointers = {}
    for node in leafs:
        # Assumption: an addr that has no value means a pointer.
        if node.addr and not node.value:
            pointers[node.load_addr] = node.path

    options = lldb.SBExpressionOptions()
    options.SetLanguage(lldb.eLanguageTypeC)
    def isHeap(addr):
        lookup = '(int)malloc_size({})'.format(addr)
        return self.context.frame.EvaluateExpression(lookup, options).unsigned != 0

    allocations = (addr for addr in pointers if isHeap(addr))
    for addr in allocations:
        print >>self.result, '0x{addr:x} {path}'.format(addr=addr, path=pointers[addr])
    if not allocations:
        print >>self.result, "No heap addresses found"


class FBSequenceCommand(fb.FBCommand):
  def name(self):
    return 'sequence'

  def description(self):
    return 'Run commands in sequence, stopping on any error.'

  def lex(self, commandLine):
    return commandLine.split(';')

  def run(self, arguments, options):
    interpreter = lldb.debugger.GetCommandInterpreter()
    # The full unsplit command is in position 0.
    sequence = arguments[1:]
    for command in sequence:
      command = command.strip()
      if not command:
        continue
      object = lldb.SBCommandReturnObject()
      interpreter.HandleCommand(command, self.context, object)
      if object.GetOutput():
        print >>self.result, object.GetOutput().strip()

      if not object.Succeeded():
        if object.GetError():
          self.result.SetError(object.GetError())
        self.result.SetStatus(object.GetStatus())
        return

class FBEvaluateFile(fb.FBCommand):
  def name(self):
    return 'evalfile'

  def description(self):
    return 'Run expression from a file.'

  def args(self):
    return [ fb.FBCommandArgument(arg='file path', type='string', help='file of source code') ]

  def getValue(self, arguments, index):
    if index >= len(arguments):
      return None
    return arguments[index]

  def run(self, arguments, options):
    file_path = arguments[0].split()[0]
    if not file_path:
      print "Error: Missing file"
      return

    file = open(file_path, 'r')
    source = file.read()
    source = string.Template(source).substitute(
      arg0=self.getValue(arguments, 1),
      arg1=self.getValue(arguments, 2),
      arg2=self.getValue(arguments, 3),
      arg3=self.getValue(arguments, 4)
    )

    ret = fb.evaluate(source)
    # if ret is not an address then print it directly
    if ret[0:2] != '0x':
      print ret
    else:
      command = 'po {}'.format(ret)
      lldb.debugger.HandleCommand(command)

