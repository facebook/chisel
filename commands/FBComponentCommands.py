#!/usr/bin/python

import os

import lldb
import fblldbbase as fb
import fblldbviewhelpers as viewHelpers

def lldbcommands():
  return [
    FBComponentsDebugCommand(),
    FBComponentsPrintCommand(),
    FBComponentsReflowCommand(),
  ]


class FBComponentsDebugCommand(fb.FBCommand):
  def name(self):
    return 'dcomponents'

  def description(self):
    return 'Set debugging options for components.'

  def options(self):
    return [
      fb.FBCommandArgument(short='-s', long='--set', arg='set', help='Set debug mode for components', boolean=True),
      fb.FBCommandArgument(short='-u', long='--unset', arg='unset', help='Unset debug mode for components', boolean=True),
    ]

  def run(self, arguments, options):
    if options.set:
      fb.evaluateEffect('[CKComponentDebugController setDebugMode:YES]')
      print 'Debug mode for ComponentKit has been set.'
    elif options.unset:
      fb.evaluateEffect('[CKComponentDebugController setDebugMode:NO]')
      print 'Debug mode for ComponentKit has been unset.'
    else:
      print 'No option for ComponentKit Debug mode specified.'

class FBComponentsPrintCommand(fb.FBCommand):
  def name(self):
    return 'pcomponents'

  def description(self):
    return 'Print a recursive description of components found starting from <aView>.'

  def options(self):
    return [
      fb.FBCommandArgument(short='-u', long='--up', arg='upwards', boolean=True, default=False, help='Print only the component hierarchy found on the first superview that has them, carrying the search up to its window.'),
      fb.FBCommandArgument(short='-v', long='--show-views', arg='showViews', type='BOOL', default='YES', help='Prints the component hierarchy and does not print the views if the supplied argument is \'NO\'. Supply either a \'YES\' or a \'NO\'. The default is to show views.'),
    ]

  def args(self):
    return [ fb.FBCommandArgument(arg='aView', type='UIView* or CKComponent*', help='The view or component from which the search for components begins.', default='(id)[[UIApplication sharedApplication] keyWindow]') ]

  def run(self, arguments, options):
    upwards = 'YES' if options.upwards else 'NO'
    showViews = 'YES' if options.showViews == 'YES' else 'NO'

    view = fb.evaluateInputExpression(arguments[0])
    if not viewHelpers.isView(view):
        # assume it's a CKComponent
        view = fb.evaluateExpression('((CKComponent *)%s).viewContext.view' % view)

    print fb.describeObject('[CKComponentHierarchyDebugHelper componentHierarchyDescriptionForView:(UIView *)' + view + ' searchUpwards:' + upwards + ' showViews:' + showViews + ']')

class FBComponentsReflowCommand(fb.FBCommand):
  def name(self):
    return 'rcomponents'

  def description(self):
    return 'Synchronously reflow and update all components.'

  def run(self, arguments, options):
    fb.evaluateEffect('[CKComponentDebugController reflowComponents]')
