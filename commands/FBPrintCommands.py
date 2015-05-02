#!/usr/bin/python

# Copyright (c) 2014, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

import os
import re

import lldb
import fblldbbase as fb
import fblldbviewcontrollerhelpers as vcHelpers
import fblldbviewhelpers as viewHelpers
import fblldbobjcruntimehelpers as runtimeHelpers

def lldbcommands():
  return [
    FBPrintViewHierarchyCommand(),
    FBPrintCoreAnimationTree(),
    FBPrintViewControllerHierarchyCommand(),
    FBPrintIsExecutingInAnimationBlockCommand(),
    FBPrintInheritanceHierarchy(),
    FBPrintUpwardResponderChain(),
    FBPrintOnscreenTableView(),
    FBPrintOnscreenTableViewCells(),
    FBPrintInternals(),
    FBPrintInstanceVariable(),
    FBPrintKeyPath(),
    FBPrintApplicationDocumentsPath(),
    FBPrintData(),
  ]

class FBPrintViewHierarchyCommand(fb.FBCommand):
  def name(self):
    return 'pviews'

  def description(self):
    return 'Print the recursion description of <aView>.'

  def options(self):
    return [
      fb.FBCommandArgument(short='-u', long='--up', arg='upwards', boolean=True, default=False, help='Print only the hierarchy directly above the view, up to its window.'),
      fb.FBCommandArgument(short='-d', long='--depth', arg='depth', type='int', default="0", help='Print only to a given depth. 0 indicates infinite depth.'),
    ]

  def args(self):
    return [ fb.FBCommandArgument(arg='aView', type='UIView*/NSView*', help='The view to print the description of.', default='__keyWindow_dynamic__') ]

  def run(self, arguments, options):
    maxDepth = int(options.depth)
    isMac = runtimeHelpers.isMacintoshArch()

    if arguments[0] == '__keyWindow_dynamic__':
      arguments[0] = '(id)[[UIApplication sharedApplication] keyWindow]'

      if isMac:
        arguments[0] = '(id)[[[[NSApplication sharedApplication] windows] objectAtIndex:0] contentView]'

    if options.upwards:
      view = arguments[0]
      description = viewHelpers.upwardsRecursiveDescription(view, maxDepth)
      if description:
        print description
      else:
        print 'Failed to walk view hierarchy. Make sure you pass a view, not any other kind of object or expression.'
    else:
      printingMethod = 'recursiveDescription'
      if isMac:
        printingMethod = '_subtreeDescription'

      description = fb.evaluateExpressionValue('(id)[' + arguments[0] + ' ' + printingMethod + ']').GetObjectDescription()
      if maxDepth > 0:
        separator = re.escape("   | ")
        prefixToRemove = separator * maxDepth + " "
        description += "\n"
        description = re.sub(r'%s.*\n' % (prefixToRemove), r'', description)
      print description


class FBPrintCoreAnimationTree(fb.FBCommand):
  def name(self):
    return 'pca'

  def description(self):
    return 'Print layer tree from the perspective of the render server.'

  def run(self, arguments, options):
    lldb.debugger.HandleCommand('expr -O -l objc++ -- [NSString stringWithCString:(char *)CARenderServerGetInfo(0, 2, 0)]')


class FBPrintViewControllerHierarchyCommand(fb.FBCommand):
  def name(self):
    return 'pvc'

  def description(self):
    return 'Print the recursion description of <aViewController>.'

  def args(self):
    return [ fb.FBCommandArgument(arg='aViewController', type='UIViewController*', help='The view controller to print the description of.', default='__keyWindow_rootVC_dynamic__') ]

  def run(self, arguments, options):
    isMac = runtimeHelpers.isMacintoshArch()

    if arguments[0] == '__keyWindow_rootVC_dynamic__':
      if fb.evaluateBooleanExpression('[UIViewController respondsToSelector:@selector(_printHierarchy)]'):
        lldb.debugger.HandleCommand('expr -O -l objc++ -- [UIViewController _printHierarchy]')
        return

      arguments[0] = '(id)[(id)[[UIApplication sharedApplication] keyWindow] rootViewController]'
      if isMac:
        arguments[0] = '(id)[[[[NSApplication sharedApplication] windows] objectAtIndex:0] contentViewController]'

    print vcHelpers.viewControllerRecursiveDescription(arguments[0])


class FBPrintIsExecutingInAnimationBlockCommand(fb.FBCommand):
  def name(self):
    return 'panim'

  def description(self):
    return 'Prints if the code is currently execution with a UIView animation block.'

  def run(self, arguments, options):
    lldb.debugger.HandleCommand('p (BOOL)[UIView _isInAnimationBlock]')


def _printIterative(initialValue, generator):
  indent = 0
  for currentValue in generator(initialValue):
    print '   | ' * indent + currentValue
    indent += 1


class FBPrintInheritanceHierarchy(fb.FBCommand):
  def name(self):
    return 'pclass'

  def description(self):
    return 'Print the inheritance starting from an instance of any class.'

  def args(self):
    return [ fb.FBCommandArgument(arg='object', type='id', help='The instance to examine.') ]

  def run(self, arguments, options):
    _printIterative(arguments[0], _inheritanceHierarchy)

def _inheritanceHierarchy(instanceOfAClass):
  instanceAddress = fb.evaluateExpression(instanceOfAClass)
  instanceClass = fb.evaluateExpression('(id)[(id)' + instanceAddress + ' class]')
  while int(instanceClass, 16):
    yield fb.evaluateExpressionValue(instanceClass).GetObjectDescription()
    instanceClass = fb.evaluateExpression('(id)[(id)' + instanceClass + ' superclass]')


class FBPrintUpwardResponderChain(fb.FBCommand):
  def name(self):
    return 'presponder'

  def description(self):
    return 'Print the responder chain starting from a specific responder.'

  def args(self):
    return [ fb.FBCommandArgument(arg='startResponder', type='UIResponder *', help='The responder to use to start walking the chain.') ]

  def run(self, arguments, options):
    startResponder = arguments[0]
    if not fb.evaluateBooleanExpression('(BOOL)[(id)' + startResponder + ' isKindOfClass:[UIResponder class]]') and not fb.evaluateBooleanExpression('(BOOL)[(id)' + startResponder + ' isKindOfClass:[NSResponder class]]'):
      print 'Whoa, ' + startResponder + ' is not a UI/NSResponder. =('
      return

    _printIterative(startResponder, _responderChain)

def _responderChain(startResponder):
  responderAddress = fb.evaluateExpression(startResponder)
  while int(responderAddress, 16):
    yield fb.evaluateExpressionValue(responderAddress).GetObjectDescription()
    responderAddress = fb.evaluateExpression('(id)[(id)' + responderAddress + ' nextResponder]')


def tableViewInHierarchy():
  viewDescription = fb.evaluateExpressionValue('(id)[(id)[[UIApplication sharedApplication] keyWindow] recursiveDescription]').GetObjectDescription()

  searchView = None

  # Try to find an instance of
  classPattern = re.compile(r'UITableView: (0x[0-9a-fA-F]+);')
  for match in re.finditer(classPattern, viewDescription):
    searchView = match.group(1)
    break

  # Try to find a direct subclass
  if not searchView:
    subclassPattern = re.compile(r'(0x[0-9a-fA-F]+); baseClass = UITableView;')
    for match in re.finditer(subclassPattern, viewDescription):
      searchView = match.group(1)
      break

  # SLOW: check every pointer in town
  if not searchView:
    pattern = re.compile(r'(0x[0-9a-fA-F]+)[;>]')
    for (view) in re.findall(pattern, viewDescription):
      if fb.evaluateBooleanExpression('[' + view + ' isKindOfClass:(id)[UITableView class]]'):
        searchView = view
        break

  return searchView

class FBPrintOnscreenTableView(fb.FBCommand):
  def name(self):
    return 'ptv'

  def description(self):
    return 'Print the highest table view in the hierarchy.'

  def run(self, arguments, options):
    tableView = tableViewInHierarchy()
    if tableView:
      viewValue = fb.evaluateExpressionValue(tableView)
      print viewValue.GetObjectDescription()
      cmd = 'echo %s | tr -d "\n" | pbcopy' % tableView
      os.system(cmd)
    else:
      print 'Sorry, chump. I couldn\'t find a table-view. :\'('

class FBPrintOnscreenTableViewCells(fb.FBCommand):
  def name(self):
    return 'pcells'

  def description(self):
    return 'Print the visible cells of the highest table view in the hierarchy.'

  def run(self, arguments, options):
    tableView = tableViewInHierarchy()
    print fb.evaluateExpressionValue('(id)[(id)' + tableView + ' visibleCells]').GetObjectDescription()


class FBPrintInternals(fb.FBCommand):
  def name(self):
    return 'pinternals'

  def description(self):
    return 'Show the internals of an object by dereferencing it as a pointer.'

  def args(self):
    return [ fb.FBCommandArgument(arg='object', type='id', help='Object expression to be evaluated.') ]

  def run(self, arguments, options):
    object = fb.evaluateObjectExpression(arguments[0])
    objectClass = fb.evaluateExpressionValue('(id)[(id)(' + object + ') class]').GetObjectDescription()

    command = 'p *(({} *)((id){}))'.format(objectClass, object)
    lldb.debugger.HandleCommand(command)


class FBPrintInstanceVariable(fb.FBCommand):
  def name(self):
    return 'pivar'

  def description(self):
    return "Print the value of an object's named instance variable."

  def args(self):
    return [
      fb.FBCommandArgument(arg='object', type='id', help='Object expression to be evaluated.'),
      fb.FBCommandArgument(arg='ivarName', help='Name of instance variable to print.')
    ]

  def run(self, arguments, options):
    commandForObject, ivarName = arguments

    object = fb.evaluateObjectExpression(commandForObject)
    objectClass = fb.evaluateExpressionValue('(id)[(' + object + ') class]').GetObjectDescription()

    ivarTypeCommand = '((char *)ivar_getTypeEncoding((void*)object_getInstanceVariable((id){}, \"{}\", 0)))[0]'.format(object, ivarName)
    ivarTypeEncodingFirstChar = fb.evaluateExpression(ivarTypeCommand)

    printCommand = 'po' if ('@' in ivarTypeEncodingFirstChar) else 'p'
    lldb.debugger.HandleCommand('{} (({} *)({}))->{}'.format(printCommand, objectClass, object, ivarName))

class FBPrintKeyPath(fb.FBCommand):
  def name(self):
    return 'pkp'

  def description(self):
    return "Print out the value of the key path expression using -valueForKeyPath:"

  def args(self):
    return [
      fb.FBCommandArgument(arg='keypath', type='NSString *', help='The keypath to print'),
    ]

  def run(self, arguments, options):
    command = arguments[0]
    if len(command.split('.')) == 1:
      lldb.debugger.HandleCommand("po " + command)
    else:
      objectToMessage, keypath = command.split('.', 1)
      object = fb.evaluateObjectExpression(objectToMessage)
      printCommand = 'po [{} valueForKeyPath:@"{}"]'.format(object, keypath)
      lldb.debugger.HandleCommand(printCommand)


class FBPrintApplicationDocumentsPath(fb.FBCommand):
  def name(self):
    return 'pdocspath'

  def description(self):
    return "Print application's 'Documents' directory path."
  
  def options(self):
    return [
      fb.FBCommandArgument(short='-o', long='--open', arg='open', boolean=True, default=False, help='open in Finder'),
    ]

  def run(self, arguments, options):
    # in iOS SDK NSDocumentDirectory == 9  NSUserDomainMask == 1 
    NSDocumentDirectory = '9' 
    NSUserDomainMask = '1'
    path = fb.evaluateExpressionValue('(NSString*)[NSSearchPathForDirectoriesInDomains(' + NSDocumentDirectory + ', ' + NSUserDomainMask + ', YES) lastObject]')
    pathString = '{}'.format(path).split('"')[1]
    cmd = 'echo {} | tr -d "\n" | pbcopy'.format(pathString)
    os.system(cmd)
    print pathString
    if options.open:
      os.system('open '+ pathString)
      

class FBPrintData(fb.FBCommand):
  def name(self):
    return 'pdata'

  def description(self):
    return 'Print the contents of NSData object as string.\n' \
           'Supported encodings:\n' \
           '- ascii,\n' \
           '- utf8,\n' \
           '- utf16, unicode,\n' \
           '- utf16l (Little endian),\n' \
           '- utf16b (Big endian),\n' \
           '- utf32,\n' \
           '- utf32l (Little endian),\n' \
           '- utf32b (Big endian),\n' \
           '- latin1, iso88591 (88591),\n' \
           '- latin2, iso88592 (88592),\n' \
           '- cp1251 (1251),\n' \
           '- cp1252 (1252),\n' \
           '- cp1253 (1253),\n' \
           '- cp1254 (1254),\n' \
           '- cp1250 (1250),' \

  def options(self):
    return [
      fb.FBCommandArgument(arg='encoding', short='-e', long='--encoding', type='string', help='Used encoding (default utf-8).', default='utf-8')
    ]

  def args(self):
    return [
      fb.FBCommandArgument(arg='data', type='NSData *', help='NSData object.')
    ]

  def run(self, arguments, option):
    # Normalize encoding.
    encoding_text = option.encoding.lower().replace(' -', '')
    enc = 4  # Default encoding UTF-8.
    if encoding_text == 'ascii':
      enc = 1
    elif encoding_text == 'utf8':
      enc = 4
    elif encoding_text == 'latin1' or encoding_text == '88591' or encoding_text == 'iso88591':
      enc = 5
    elif encoding_text == 'latin2' or encoding_text == '88592' or encoding_text == 'iso88592':
      enc = 9
    elif encoding_text == 'unicode' or encoding_text == 'utf16':
      enc = 10
    elif encoding_text == '1251' or encoding_text == 'cp1251':
      enc = 11
    elif encoding_text == '1252' or encoding_text == 'cp1252':
      enc = 12
    elif encoding_text == '1253' or encoding_text == 'cp1253':
      enc = 13
    elif encoding_text == '1254' or encoding_text == 'cp1254':
      enc = 14
    elif encoding_text == '1250' or encoding_text == 'cp1250':
      enc = 15
    elif encoding_text == 'utf16b':
      enc = 0x90000100
    elif encoding_text == 'utf16l':
      enc = 0x94000100
    elif encoding_text == 'utf32':
      enc = 0x8c000100
    elif encoding_text == 'utf32b':
      enc = 0x98000100
    elif encoding_text == 'utf32l':
      enc = 0x9c000100

    print_command = 'po (NSString *)[[NSString alloc] initWithData:{} encoding:{}]'.format(arguments[0], enc)
    lldb.debugger.HandleCommand(print_command)
