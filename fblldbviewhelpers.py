#!/usr/bin/python

# Copyright (c) 2014, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

import lldb

import fblldbbase as fb

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
    raise Exception('Argument must be a CALayer or a UIView')

