#!/usr/bin/python

# Copyright (c) 2014, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

import os
import time

import lldb
import fblldbbase as fb
import fblldbviewhelpers as viewHelpers
import fblldbinputhelpers as inputHelpers

def lldbcommands():
  return [
    FBFlickerViewCommand(),
    FBViewSearchCommand(),
  ]


class FBFlickerViewCommand(fb.FBCommand):
  def name(self):
    return 'flicker'

  def description(self):
    return 'Quickly show and hide a view to quickly help visualize where it is.'

  def args(self):
    return [ fb.FBCommandArgument(arg='viewOrLayer', type='UIView*', help='The view to border.') ]

  def run(self, arguments, options):
    object = fb.evaluateObjectExpression(arguments[0])

    isHidden = fb.evaluateBooleanExpression('[' + object + ' isHidden]')
    shouldHide = not isHidden
    for x in range(0, 2):
      viewHelpers.setViewHidden(object, shouldHide)
      viewHelpers.setViewHidden(object, isHidden)


class FBViewSearchCommand(fb.FBCommand):
  def name(self):
    return 'vs'

  def description(self):
    return 'Interactively search for a view by walking the hierarchy.'

  def args(self):
    return [ fb.FBCommandArgument(arg='view', type='UIView*', help='The view to border.') ]

  def run(self, arguments, options):
    print '\nUse the following and (q) to quit.\n(w) move to superview\n(s) move to first subview\n(a) move to previous sibling\n(d) move to next sibling\n(p) print the hierarchy\n'

    object = fb.evaluateObjectExpression(arguments[0])
    walker = FlickerWalker(object)
    walker.run()

class FlickerWalker:
  def __init__(self, startView):
    self.setCurrentView(startView)

    self.handler = inputHelpers.FBInputHandler(lldb.debugger, self.inputCallback)
    self.handler.start()

  def run(self):
    while self.handler.isValid():
      self.flicker()

  def flicker(self):
    viewHelpers.setViewHidden(self.currentView, True)
    time.sleep(0.1)
    viewHelpers.setViewHidden(self.currentView, False)
    time.sleep(0.3)

  def inputCallback(self, input):
    oldView = self.currentView

    if input == 'q':
      cmd = 'echo %s | tr -d "\n" | pbcopy' % oldView
      os.system(cmd)

      print '\nI hope ' + oldView + ' was what you were looking for. I put it on your clipboard.'

      self.handler.stop()
    elif input == 'w':
      v = superviewOfView(self.currentView)
      if not v:
        print 'There is no superview. Where are you trying to go?!'
      self.setCurrentView(v)
    elif input == 's':
      v = firstSubviewOfView(self.currentView)
      if not v:
        print '\nThe view has no subviews.\n'
      self.setCurrentView(v)
    elif input == 'd':
      v = nthSiblingOfView(self.currentView, -1)
      if v == oldView:
        print '\nThere are no sibling views to this view.\n'
      self.setCurrentView(v)
    elif input == 'a':
      v = nthSiblingOfView(self.currentView, 1)
      if v == oldView:
        print '\nThere are no sibling views to this view.\n'
      self.setCurrentView(v)
    elif input == 'p':
      lldb.debugger.HandleCommand('po [(id)' + oldView + ' recursiveDescription]')
    else:
      print '\nI really have no idea what you meant by \'' + input + '\'... =\\\n'

    viewHelpers.setViewHidden(oldView, False)

  def setCurrentView(self, view):
    if view:
      self.currentView = view
      lldb.debugger.HandleCommand('po (id)' + view)

def superviewOfView(view):
  superview = fb.evaluateObjectExpression('[' + view + ' superview]')
  if int(superview, 16) == 0:
    return None

  return superview

def subviewsOfView(view):
  return fb.evaluateObjectExpression('[' + view + ' subviews]')

def firstSubviewOfView(view):
  subviews = subviewsOfView(view)
  numViews = fb.evaluateIntegerExpression('[(id)' + subviews + ' count]')

  if numViews == 0:
    return None
  else:
    return fb.evaluateObjectExpression('[' + subviews + ' objectAtIndex:0]')

def nthSiblingOfView(view, n):
  subviews = subviewsOfView(superviewOfView(view))
  numViews = fb.evaluateIntegerExpression('[(id)' + subviews + ' count]')

  idx = fb.evaluateIntegerExpression('[(id)' + subviews + ' indexOfObject:' + view + ']')

  newIdx = idx + n
  while newIdx < 0:
    newIdx += numViews
  newIdx = newIdx % numViews

  return fb.evaluateObjectExpression('[(id)' + subviews + ' objectAtIndex:' + str(newIdx) + ']')
