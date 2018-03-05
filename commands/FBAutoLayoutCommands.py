#!/usr/bin/python

# Copyright (c) 2014, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.


import lldb
import fblldbbase as fb
import fblldbviewhelpers as viewHelpers

def lldbcommands():
  return [
    FBPrintAutolayoutTrace(),
    FBAutolayoutBorderAmbiguous(),
    FBAutolayoutUnborderAmbiguous(),
  ]

class FBPrintAutolayoutTrace(fb.FBCommand):
  def name(self):
    return 'paltrace'

  def description(self):
    return "Print the Auto Layout trace for the given view. Defaults to the key window."

  def args(self):
    return [ fb.FBCommandArgument(arg='view', type='UIView *', help='The view to print the Auto Layout trace for.', default='(id)[[UIApplication sharedApplication] keyWindow]') ]

  def run(self, arguments, options):
    view = fb.evaluateInputExpression(arguments[0])
    opt = fb.evaluateBooleanExpression('[UIView instancesRespondToSelector:@selector(_autolayoutTraceRecursively:)]')
    traceCall = '_autolayoutTraceRecursively:1' if opt else '_autolayoutTrace'
    print fb.describeObject('[{} {}]'.format(view, traceCall))


def setBorderOnAmbiguousViewRecursive(view, width, color):
  if not fb.evaluateBooleanExpression('[(id)%s isKindOfClass:(Class)[UIView class]]' % view):
    return

  isAmbiguous = fb.evaluateBooleanExpression('(BOOL)[%s hasAmbiguousLayout]' % view)
  if isAmbiguous:
    layer = viewHelpers.convertToLayer(view)
    fb.evaluateEffect('[%s setBorderWidth:(CGFloat)%s]' % (layer, width))
    fb.evaluateEffect('[%s setBorderColor:(CGColorRef)[(id)[UIColor %sColor] CGColor]]' % (layer, color))

  subviews = fb.evaluateExpression('(id)[%s subviews]' % view)
  subviewsCount = int(fb.evaluateExpression('(int)[(id)%s count]' % subviews))
  if subviewsCount > 0:
    for i in range(0, subviewsCount):
      subview = fb.evaluateExpression('(id)[%s objectAtIndex:%i]' % (subviews, i))
      setBorderOnAmbiguousViewRecursive(subview, width, color)


class FBAutolayoutBorderAmbiguous(fb.FBCommand):
  def name(self):
    return 'alamborder'

  def description(self):
    return "Put a border around views with an ambiguous layout"

  def options(self):
    return [
      fb.FBCommandArgument(short='-c', long='--color', arg='color', type='string', default='red', help='A color name such as \'red\', \'green\', \'magenta\', etc.'),
      fb.FBCommandArgument(short='-w', long='--width', arg='width', type='CGFloat', default=2.0, help='Desired width of border.')
    ]

  def run(self, arguments, options):
    keyWindow = fb.evaluateExpression('(id)[[UIApplication sharedApplication] keyWindow]')
    setBorderOnAmbiguousViewRecursive(keyWindow, options.width, options.color)
    lldb.debugger.HandleCommand('caflush')


class FBAutolayoutUnborderAmbiguous(fb.FBCommand):
  def name(self):
    return 'alamunborder'

  def description(self):
    return "Removes the border around views with an ambiguous layout"

  def run(self, arguments, options):
    keyWindow = fb.evaluateExpression('(id)[[UIApplication sharedApplication] keyWindow]')
    setBorderOnAmbiguousViewRecursive(keyWindow, 0, "red")
    lldb.debugger.HandleCommand('caflush')
