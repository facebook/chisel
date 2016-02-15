#!/usr/bin/python

# Copyright (c) 2016, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

import os

import lldb
import fblldbbase as fb
import fblldbviewhelpers as viewHelpers

ACCESSIBILITY_ID = 0
REPLACEMENT_TEXT = 1


def lldbcommands():
  return [
    FBInputTextCommand(),
  ]


class FBInputTextCommand(fb.FBCommand):
  def name(self):
    return 'input'

  def description(self):
    return 'Input text into text field or text view by accessibility id.'

  def args(self):
    return [
      fb.FBCommandArgument(arg='accessibilityId', type='string', help='The accessibility ID of the input view.'),
      fb.FBCommandArgument(arg='replacementText', type='string', help='The text to set.')
    ]

  def run(self, arguments, options):
    rootView = fb.evaluateObjectExpression('[[UIApplication sharedApplication] keyWindow]')
    self.findView(rootView, arguments[ACCESSIBILITY_ID], arguments[REPLACEMENT_TEXT])

  def findView(self, view, searchIdentifier, replacementText):
    views = self.subviewsOfView(view)
    for index in range(0, self.viewsCount(views)):
        subview = self.subviewAtIndex(views, index)
        self.findView(subview, searchIdentifier, replacementText)
    else:
      identifier = self.accessibilityIdentifier(view)
      if self.isEqualToString(identifier, searchIdentifier):
        self.setTextInView(view, replacementText)

# Some helpers
  def subviewsOfView(self, view):
    return fb.evaluateObjectExpression('[%s subviews]' % view)

  def subviewAtIndex(self, views, index):
    return fb.evaluateObjectExpression('[%s objectAtIndex:%i]' % (views, index))

  def viewsCount(self, views):
    return int(fb.evaluateExpression('(int)[%s count]' % views))

  def accessibilityIdentifier(self, view):
    return fb.evaluateObjectExpression('[%s accessibilityIdentifier]' % view)

  def isEqualToString(self, identifier, needle):
    return fb.evaluateBooleanExpression('[%s isEqualToString:@"%s"]' % (identifier, needle))

  def setTextInView(self, view, text):
    fb.evaluateObjectExpression('[%s setText:@"%s"]' % (view, text))
    viewHelpers.flushCoreAnimationTransaction()
