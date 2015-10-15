#!/usr/bin/python

# Copyright (c) 2015, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

import re
import os

import lldb
import fblldbbase as fb
import fblldbobjecthelpers as objHelpers

# This is the key corresponding to accessibility label in _accessibilityElementsInContainer:
ACCESSIBILITY_LABEL_KEY = 2001

def lldbcommands():
  return [
    FBPrintAccessibilityLabels(),
    FBFindViewByAccessibilityLabelCommand(),
  ]

class FBPrintAccessibilityLabels(fb.FBCommand):
  def name(self):
    return 'pa11y'

  def description(self):
    return 'Print accessibility labels of all views in hierarchy of <aView>'

  def args(self):
    return [ fb.FBCommandArgument(arg='aView', type='UIView*', help='The view to print the hierarchy of.', default='(id)[[UIApplication sharedApplication] keyWindow]') ]

  def run(self, arguments, options):
    forceStartAccessibilityServer();
    printAccessibilityHierarchy(arguments[0])

class FBFindViewByAccessibilityLabelCommand(fb.FBCommand):
  def name(self):
    return 'fa11y'

  def description(self):
    return 'Find the views whose accessibility labels match labelRegex and puts the address of the first result on the clipboard.'

  def args(self):
    return [ fb.FBCommandArgument(arg='labelRegex', type='string', help='The accessibility label regex to search the view hierarchy for.') ]

  def accessibilityGrepHierarchy(self, view, needle):
    a11yLabel = accessibilityLabel(view)
    #if we don't have any accessibility string - we should have some children
    if int(a11yLabel.GetValue(), 16) == 0:
      #We call private method that gives back all visible accessibility children for view
      accessibilityElements = fb.evaluateObjectExpression('[[[UIApplication sharedApplication] keyWindow] _accessibilityElementsInContainer:0 topLevel:%s includeKB:0]' % view)
      accessibilityElementsCount = fb.evaluateIntegerExpression('[%s count]' % accessibilityElements)
      for index in range(0, accessibilityElementsCount):
        subview = fb.evaluateObjectExpression('[%s objectAtIndex:%i]' % (accessibilityElements, index))
        self.accessibilityGrepHierarchy(subview, needle)
    elif re.match(r'.*' + needle + '.*', a11yLabel.GetObjectDescription(), re.IGNORECASE):
      classDesc = objHelpers.className(view)
      print('({} {}) {}'.format(classDesc, view, a11yLabel.GetObjectDescription()))

      #First element that is found is copied to clipboard
      if not self.foundElement:
        self.foundElement = True
        cmd = 'echo %s | tr -d "\n" | pbcopy' % view
        os.system(cmd)

  def run(self, arguments, options):
    forceStartAccessibilityServer()
    rootView = fb.evaluateObjectExpression('[[UIApplication sharedApplication] keyWindow]')
    self.foundElement = False
    self.accessibilityGrepHierarchy(rootView, arguments[0])

def forceStartAccessibilityServer():
  #We try to start accessibility server only if we don't have needed method active
  if not fb.evaluateBooleanExpression('[UIView instancesRespondToSelector:@selector(_accessibilityElementsInContainer:)]'):
    #Starting accessibility server is different for simulator and device
    if fb.evaluateExpressionValue('(id)[[UIDevice currentDevice] model]').GetObjectDescription().lower().find('simulator') >= 0:
      lldb.debugger.HandleCommand('expr (void)[[UIApplication sharedApplication] accessibilityActivate]')
    else:
      lldb.debugger.HandleCommand('expr (void)[[[UIApplication sharedApplication] _accessibilityBundlePrincipalClass] _accessibilityStartServer]')

def accessibilityLabel(view):
  #using Apple private API to get real value of accessibility string for element.
  return fb.evaluateExpressionValue('(id)[%s accessibilityAttributeValue:%i]' % (view, ACCESSIBILITY_LABEL_KEY), False)

def printAccessibilityHierarchy(view, indent = 0):
  a11yLabel = accessibilityLabel(view)
  classDesc = objHelpers.className(view)
  indentString = '   | ' * indent

  #if we don't have any accessibility string - we should have some children
  if int(a11yLabel.GetValue(), 16) == 0:
    print indentString + ('{} {}'.format(classDesc, view))
    #We call private method that gives back all visible accessibility children for view
    accessibilityElements = fb.evaluateObjectExpression('[[[UIApplication sharedApplication] keyWindow] _accessibilityElementsInContainer:0 topLevel:%s includeKB:0]' % view)
    accessibilityElementsCount = fb.evaluateIntegerExpression('(int)[%s count]' % accessibilityElements)
    for index in range(0, accessibilityElementsCount):
      subview = fb.evaluateObjectExpression('[%s objectAtIndex:%i]' % (accessibilityElements, index))
      printAccessibilityHierarchy(subview, indent + 1)
  else:
    print indentString + ('({} {}) {}'.format(classDesc, view, a11yLabel.GetObjectDescription()))


