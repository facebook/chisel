#!/usr/bin/python

# Copyright (c) 2014, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

import lldb
import os
import time

import fblldbviewhelpers as viewHelpers
import fblldbbase as fb

def lldbcommands():
  return [
    FBCoreAnimationFlushCommand(),
    FBDrawBorderCommand(),
    FBRemoveBorderCommand(),
    FBMaskViewCommand(),
    FBUnmaskViewCommand(),
    FBShowViewCommand(),
    FBHideViewCommand(),
  ]


class FBDrawBorderCommand(fb.FBCommand):
  def name(self):
    return 'border'

  def description(self):
    return 'Draws a border around <viewOrLayer>. Color and width can be optionally provided.'

  def args(self):
    return [ fb.FBCommandArgument(arg='viewOrLayer', type='UIView/CALayer *', help='The view/layer to border.') ]

  def options(self):
    return [
      fb.FBCommandArgument(short='-c', long='--color', arg='color', type='string', default='red', help='A color name such as \'red\', \'green\', \'magenta\', etc.'),
      fb.FBCommandArgument(short='-w', long='--width', arg='width', type='CGFloat', default=2.0, help='Desired width of border.')
    ]

  def run(self, args, options):
    layer = viewHelpers.convertToLayer(args[0])
    lldb.debugger.HandleCommand('expr (void)[%s setBorderWidth:%s]' % (layer, options.width))
    lldb.debugger.HandleCommand('expr (void)[%s setBorderColor:(CGColorRef)[(id)[UIColor %sColor] CGColor]]' % (layer, options.color))
    lldb.debugger.HandleCommand('caflush')


class FBRemoveBorderCommand(fb.FBCommand):
  def name(self):
    return 'unborder'

  def description(self):
    return 'Removes border around <viewOrLayer>.'

  def args(self):
    return [ fb.FBCommandArgument(arg='viewOrLayer', type='UIView/CALayer *', help='The view/layer to unborder.') ]

  def run(self, args, options):
    layer = viewHelpers.convertToLayer(args[0])
    lldb.debugger.HandleCommand('expr (void)[%s setBorderWidth:%s]' % (layer, 0))
    lldb.debugger.HandleCommand('caflush')


class FBMaskViewCommand(fb.FBCommand):
  def name(self):
    return 'mask'

  def description(self):
    return 'Add a transparent rectangle to the window to reveal a possibly obscured or hidden view or layer\'s bounds'

  def args(self):
    return [ fb.FBCommandArgument(arg='viewOrLayer', type='UIView/CALayer *', help='The view/layer to mask.') ]

  def options(self):
    return [
      fb.FBCommandArgument(short='-c', long='--color', arg='color', type='string', default='red', help='A color name such as \'red\', \'green\', \'magenta\', etc.'),
      fb.FBCommandArgument(short='-a', long='--alpha', arg='alpha', type='CGFloat', default=0.5, help='Desired alpha of mask.')
    ]

  def run(self, args, options):
    viewOrLayer = fb.evaluateObjectExpression(args[0])
    viewHelpers.maskView(viewOrLayer, options.color, options.alpha)


class FBUnmaskViewCommand(fb.FBCommand):
  def name(self):
    return 'unmask'

  def description(self):
    return 'Remove mask from a view or layer'

  def args(self):
    return [ fb.FBCommandArgument(arg='viewOrLayer', type='UIView/CALayer *', help='The view/layer to mask.') ]

  def run(self, args, options):
    viewOrLayer = fb.evaluateObjectExpression(args[0])
    viewHelpers.unmaskView(viewOrLayer)


class FBCoreAnimationFlushCommand(fb.FBCommand):
  def name(self):
    return 'caflush'

  def description(self):
    return 'Force Core Animation to flush. This will \'repaint\' the UI but also may mess with ongoing animations.'

  def run(self, arguments, options):
    viewHelpers.flushCoreAnimationTransaction()


class FBShowViewCommand(fb.FBCommand):
  def name(self):
    return 'show'

  def description(self):
    return 'Show a view or layer.'

  def args(self):
    return [ fb.FBCommandArgument(arg='viewOrLayer', type='UIView/CALayer *', help='The view/layer to show.') ]

  def run(self, args, options):
    viewHelpers.setViewHidden(args[0], False)


class FBHideViewCommand(fb.FBCommand):
  def name(self):
    return 'hide'

  def description(self):
    return 'Hide a view or layer.'

  def args(self):
    return [ fb.FBCommandArgument(arg='viewOrLayer', type='UIView/CALayer *', help='The view/layer to hide.') ]

  def run(self, args, options):
    viewHelpers.setViewHidden(args[0], True)
