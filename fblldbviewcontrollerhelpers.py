#!/usr/bin/python

# Copyright (c) 2014, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

import lldb
import fblldbbase as fb

def viewControllerRecursiveDescription(vc):
  return _recursiveViewControllerDescriptionWithPrefixAndChildPrefix(fb.evaluateObjectExpression(vc), '', '', '')

def _viewControllerDescription(viewController):
  vc = '(%s)' % (viewController)

  if fb.evaluateBooleanExpression('[(id)%s isViewLoaded]' % (vc)):
    result = fb.evaluateExpressionValue('(id)[[NSString alloc] initWithFormat:@"<%%@: %%p; view = <%%@; %%p>; frame = (%%g, %%g; %%g, %%g)>", (id)NSStringFromClass((id)[(id)%s class]), %s, (id)[(id)[(id)%s view] class], (id)[(id)%s view], ((CGRect)[(id)[(id)%s view] frame]).origin.x, ((CGRect)[(id)[(id)%s view] frame]).origin.y, ((CGRect)[(id)[(id)%s view] frame]).size.width, ((CGRect)[(id)[(id)%s view] frame]).size.height]' % (vc, vc, vc, vc, vc, vc, vc, vc))
  else:
    result = fb.evaluateExpressionValue('(id)[[NSString alloc] initWithFormat:@"<%%@: %%p; view not loaded>", (id)NSStringFromClass((id)[(id)%s class]), %s]' % (vc, vc))

  if result.GetError() is not None and str(result.GetError()) != 'success':
    return '[Error getting description.]'
  else:
    return result.GetObjectDescription()


def _recursiveViewControllerDescriptionWithPrefixAndChildPrefix(vc, string, prefix, childPrefix):
  s = '%s%s%s\n' % (prefix, '' if prefix == '' else ' ', _viewControllerDescription(vc))

  nextPrefix = childPrefix + '   |'

  numChildViewControllers = fb.evaluateIntegerExpression('(int)[(id)[%s childViewControllers] count]' % (vc))
  childViewControllers = fb.evaluateExpression('(id)[%s childViewControllers]' % (vc))

  for i in range(0, numChildViewControllers):
    viewController = fb.evaluateExpression('(id)[(id)[%s childViewControllers] objectAtIndex:%d]' % (vc, i))
    s += _recursiveViewControllerDescriptionWithPrefixAndChildPrefix(viewController, string, nextPrefix, nextPrefix)

  isModal = fb.evaluateBooleanExpression('((id)[(id)[(id)%s presentedViewController] presentingViewController]) == %s' % (vc, vc))

  if isModal:
    modalVC = fb.evaluateObjectExpression('(id)[(id)%s presentedViewController]' % (vc))
    s += _recursiveViewControllerDescriptionWithPrefixAndChildPrefix(modalVC, string, childPrefix + '  *M' , nextPrefix)
    s += '\n// \'*M\' means the view controller is presented modally.'

  return string + s