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
import chlldbbase as ch
import chlldbviewcontrollerhelpers as vcHelpers

def lldbcommands():
  return [
    PrintViewHierarchyCommand(),
    PrintCoreAnimationTree(),
    PrintViewControllerHierarchyCommand(),
    PrintIsExecutingInAnimationBlockCommand(),
    PrintInheritanceHierarchy(),
    PrintUpwardResponderChain(),
    PrintOnscreenTableView(),
    PrintOnscreenTableViewCells(),
    PrintInternals(),
    PrintInstanceVariable(),
  ]

class PrintViewHierarchyCommand(ch.Command):
  def name(self):
    return 'pviews'

  def description(self):
    return 'Print the recursion description of <aView>.'

  def args(self):
    return [ ch.CommandArgument(arg='aView', type='UIView*', help='The view to print the description of.', default='(id)[UIWindow keyWindow]') ]

  def run(self, arguments, options):
    lldb.debugger.HandleCommand('po (id)[' + arguments[0] + ' recursiveDescription]')


class PrintCoreAnimationTree(ch.Command):
  def name(self):
    return 'pca'

  def description(self):
    return 'Print layer tree from the perspective of the render server.'

  def run(self, arguments, options):
    lldb.debugger.HandleCommand('po [NSString stringWithCString:(char *)CARenderServerGetInfo(0, 2, 0)]')


class PrintViewControllerHierarchyCommand(ch.Command):
  def name(self):
    return 'pvc'

  def description(self):
    return 'Print the recursion description of <aViewController>.'

  def args(self):
    return [ ch.CommandArgument(arg='aViewController', type='UIViewController*', help='The view controller to print the description of.', default='(id)[(id)[UIWindow keyWindow] rootViewController]') ]

  def run(self, arguments, options):
    print vcHelpers.viewControllerRecursiveDescription(arguments[0])


class PrintIsExecutingInAnimationBlockCommand(ch.Command):
  def name(self):
    return 'panim'

  def description(self):
    return 'Prints if the code is currently execution with a UIView animation block.'

  def run(self, arguments, options):
    lldb.debugger.HandleCommand('p (BOOL)[UIView _isInAnimationBlock]')


def _printIterative(initialValue, generator):
  indent = 0
  for currentValue in generator(initialValue):
    print '   | '*indent + currentValue
    indent += 1


class PrintInheritanceHierarchy(ch.Command):
  def name(self):
    return 'pclass'

  def description(self):
    return 'Print the inheritance starting from an instance of any class.'

  def args(self):
    return [ ch.CommandArgument(arg='object', type='id', help='The instance to examine.') ]

  def run(self, arguments, options):
    _printIterative(arguments[0], _inheritanceHierarchy)

def _inheritanceHierarchy(instanceOfAClass):
  instanceAddress = ch.evaluateExpression(instanceOfAClass)
  instanceClass = ch.evaluateExpression('(id)[(id)' + instanceAddress + ' class]')
  while int(instanceClass, 16):
    yield ch.evaluateExpressionValue(instanceClass).GetObjectDescription()
    instanceClass = ch.evaluateExpression('(id)[(id)' + instanceClass + ' superclass]')


class PrintUpwardResponderChain(ch.Command):
  def name(self):
    return 'presponder'

  def description(self):
    return 'Print the responder chain starting from a specific responder.'

  def args(self):
    return [ ch.CommandArgument(arg='startResponder', type='UIResponder *', help='The responder to use to start walking the chain.') ]

  def run(self, arguments, options):
    startResponder = arguments[0]
    if not ch.evaluateBooleanExpression('(BOOL)[(id)' + startResponder + ' isKindOfClass:[UIResponder class]]'):
      print 'Whoa, ' + startResponder + ' is not a UIResponder. =('
      return

    _printIterative(startResponder, _responderChain)

def _responderChain(startResponder):
  responderAddress = ch.evaluateExpression(startResponder)
  while int(responderAddress, 16):
    yield ch.evaluateExpressionValue(responderAddress).GetObjectDescription()
    responderAddress = ch.evaluateExpression('(id)[(id)' + responderAddress + ' nextResponder]')


def tableViewInHierarchy():
  viewDescription = ch.evaluateExpressionValue('(id)[(id)[UIWindow keyWindow] recursiveDescription]').GetObjectDescription()

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
      if ch.evaluateBooleanExpression('[' + view + ' isKindOfClass:(id)[UITableView class]]'):
        searchView = view
        break

  return searchView

class PrintOnscreenTableView(ch.Command):
  def name(self):
    return 'ptv'

  def description(self):
    return 'Print the highest table view in the hierarchy.'

  def run(self, arguments, options):
    tableView = tableViewInHierarchy()
    if tableView:
      viewValue = ch.evaluateExpressionValue(tableView)
      print viewValue.GetObjectDescription()
      cmd = 'echo %s | tr -d "\n" | pbcopy' % tableView
      os.system(cmd)
    else:
      print 'Sorry, chump. I couldn\'t find a table-view. :\'('

class PrintOnscreenTableViewCells(ch.Command):
  def name(self):
    return 'pcells'

  def description(self):
    return 'Print the visible cells of the highest table view in the hierarchy.'

  def run(self, arguments, options):
    tableView = tableViewInHierarchy()
    print ch.evaluateExpressionValue('(id)[(id)' + tableView + ' visibleCells]').GetObjectDescription()


class PrintInternals(ch.Command):
  def name(self):
    return 'pinternals'

  def description(self):
    return 'Show the internals of an object by dereferencing it as a pointer.'

  def args(self):
    return [ ch.CommandArgument(arg='object', type='id', help='Object expression to be evaluated.') ]

  def run(self, arguments, options):
    object = ch.evaluateObjectExpression(arguments[0])
    objectClass = ch.evaluateExpressionValue('(id)[(id)(' + object + ') class]').GetObjectDescription()

    command = 'p *(({} *)((id){}))'.format(objectClass, object)
    lldb.debugger.HandleCommand(command)


class PrintInstanceVariable(ch.Command):
  def name(self):
    return 'pivar'

  def description(self):
    return "Print the value of an object's named instance variable."

  def args(self):
    return [
      ch.CommandArgument(arg='object', type='id', help='Object expression to be evaluated.'),
      ch.CommandArgument(arg='ivarName', help='Name of instance variable to print.')
    ]

  def run(self, arguments, options):
    commandForObject, ivarName = arguments

    object = ch.evaluateObjectExpression(commandForObject)
    objectClass = ch.evaluateExpressionValue('(id)[(' + object + ') class]').GetObjectDescription()

    ivarTypeCommand = '((char *)ivar_getTypeEncoding((void *)object_getInstanceVariable((id){}, \"{}\", 0)))[0]'.format(object, ivarName)
    ivarTypeEncodingFirstChar = ch.evaluateExpression(ivarTypeCommand)

    printCommand = 'po' if ('@' in ivarTypeEncodingFirstChar) else 'p'
    lldb.debugger.HandleCommand('{} (({} *)({}))->{}'.format(printCommand, objectClass, object, ivarName))
