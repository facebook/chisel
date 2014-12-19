#!/usr/bin/python

# Copyright (c) 2014, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

import lldb
import re
import fblldbbase as fb
import fblldbobjecthelpers as objectHelpers

def flushCoreAnimationTransaction():
  lldb.debugger.HandleCommand('expr (void)[CATransaction flush]')

def setViewHidden(object, hidden):
  lldb.debugger.HandleCommand('expr (void)[' + object + ' setHidden:' + str(int(hidden)) + ']')
  flushCoreAnimationTransaction()

def maskView(viewOrLayer, color, alpha):
  unmaskView(viewOrLayer)
  window = fb.evaluateExpression('(UIWindow *)[[UIApplication sharedApplication] keyWindow]')
  origin = convertPoint(0, 0, viewOrLayer, window)
  size = fb.evaluateExpressionValue('(CGSize)((CGRect)[(id)%s frame]).size' % viewOrLayer)

  rectExpr = '(CGRect){{%s, %s}, {%s, %s}}' % (origin.GetChildMemberWithName('x').GetValue(),
                                               origin.GetChildMemberWithName('y').GetValue(),
                                               size.GetChildMemberWithName('width').GetValue(),
                                               size.GetChildMemberWithName('height').GetValue())
  mask = fb.evaluateExpression('[((UIView *)[UIView alloc]) initWithFrame:%s]' % rectExpr)

  lldb.debugger.HandleCommand('expr (void)[%s setTag:(NSInteger)%s]' % (mask, viewOrLayer))
  lldb.debugger.HandleCommand('expr (void)[%s setBackgroundColor:[UIColor %sColor]]' % (mask, color))
  lldb.debugger.HandleCommand('expr (void)[%s setAlpha:(CGFloat)%s]' % (mask, alpha))
  lldb.debugger.HandleCommand('expr (void)[%s addSubview:%s]' % (window, mask))
  flushCoreAnimationTransaction()

def unmaskView(viewOrLayer):
  window = fb.evaluateExpression('(UIWindow *)[[UIApplication sharedApplication] keyWindow]')
  mask = fb.evaluateExpression('(UIView *)[%s viewWithTag:(NSInteger)%s]' % (window, viewOrLayer))
  lldb.debugger.HandleCommand('expr (void)[%s removeFromSuperview]' % mask)
  flushCoreAnimationTransaction()

def convertPoint(x, y, fromViewOrLayer, toViewOrLayer):
  fromLayer = convertToLayer(fromViewOrLayer)
  toLayer = convertToLayer(toViewOrLayer)
  return fb.evaluateExpressionValue('(CGPoint)[%s convertPoint:(CGPoint){ .x = %s, .y = %s } toLayer:(CALayer *)%s]' % (fromLayer, x, y, toLayer))

def convertToLayer(viewOrLayer):
  if fb.evaluateBooleanExpression('[(id)%s isKindOfClass:(Class)[CALayer class]]' % viewOrLayer):
    return viewOrLayer
  elif fb.evaluateBooleanExpression('[(id)%s respondsToSelector:(SEL)@selector(layer)]' % viewOrLayer):
    return fb.evaluateExpression('(CALayer *)[%s layer]' % viewOrLayer)
  else:
    raise Exception('Argument must be a CALayer, UIView, or NSView.')

def upwardsRecursiveDescription(view, maxDepth=0):
  if not fb.evaluateBooleanExpression('[(id)%s isKindOfClass:(Class)[UIView class]]' % view) and not fb.evaluateBooleanExpression('[(id)%s isKindOfClass:(Class)[NSView class]]' % view):
    return None

  currentView = view
  recursiveDescription = []
  depth = 0

  while currentView and (maxDepth <= 0 or depth <= maxDepth):
    depth += 1

    viewDescription = fb.evaluateExpressionValue('(id)[%s debugDescription]' % (currentView)).GetObjectDescription()
    currentView = fb.evaluateExpression('(void*)[%s superview]' % (currentView))
    try:
      if int(currentView, 0) == 0:
        currentView = None
    except:
      currentView = None

    if viewDescription:
      recursiveDescription.insert(0, viewDescription)

  if len(viewDescription) == 0:
    return None

  currentPrefix = ""
  builder = ""
  for viewDescription in recursiveDescription:
    builder += currentPrefix + viewDescription + "\n"
    currentPrefix += "   | "

  return builder

# GetObjectDescription will try to return the pointer.
# However on UIAccessibilityElements, the result will look like this:
#  [UITableViewSectionElement]{0x79eb2280} section: 0 (isHeader: 1)
#  [UITableViewCellAccessibilityElement - 0x79eac160] <.....
# So, just get the first hex address
def firstHexInDescription(object):
  return re.findall(r'0x[0-9A-F]+', "{}".format(object), re.I)[0]

def accessibilityDescription(object):
  if isAccessibilityElement(object):
    return objectHelpers.displayObjectWithKeys(object, ["accessibilityLabel", "accessibilityValue", "accessibilityHint"])
  else:
    return objectHelpers.displayObjectWithString(object, "isAccessibilityElement=NO")

def isAccessibilityElement(object):
  return fb.evaluateBooleanExpression('[(id)%s isAccessibilityElement]' % object)
  
def accessibilityElementAtIndex(object, index):
  cmd = '(id)[%s accessibilityElementAtIndex:%s]' % (object, index)
  obj = firstHexInDescription(fb.evaluateExpressionValue(cmd))
  return obj

def accessibilityChildren(object):
  accessibilityCount = fb.evaluateIntegerExpression("(int)[%s accessibilityElementCount]" % (object))
  aeChildren = []
  if accessibilityCount < fb.NSNOTFOUND32BIT:
    for i in range(0, accessibilityCount):
      aeChildren.append(accessibilityElementAtIndex(object, i))
  return aeChildren

def subviews(view):
  subviewResult = []
  responds = fb.evaluateBooleanExpression('[(id)%s respondsToSelector:(SEL)@selector(subviews)]' % view)
  if responds:
    subviews = fb.evaluateExpression('(id)[%s subviews]' % view)
    subviewsCount = fb.evaluateIntegerExpression('[(id)%s count]' % subviews)
    if subviewsCount > 0:
      for i in range(0, subviewsCount):
        subview = fb.evaluateExpression('(id)[%s objectAtIndex:%i]' % (subviews, i))
        subviewResult.append(subview)
  return subviewResult

      
def accessibilityRecursiveDescription(object, prefix="", childType=""):
  print '%s%s%s' % (prefix, childType, accessibilityDescription(object))
  nextPrefix = prefix + '    |'
  aeChildren = accessibilityChildren(object)
  for ae in aeChildren:
      accessibilityRecursiveDescription(ae, nextPrefix, 'A ')

  if len(aeChildren) == 0:
    for subview in subviews(object):
      accessibilityRecursiveDescription(subview, nextPrefix, 'S ')

