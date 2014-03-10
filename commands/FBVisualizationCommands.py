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

import fblldbbase as fb

def lldbcommands():
  return [
    FBVisualizeCommand()
  ]

def _showImage(commandForImage):
  commandForImage = '(' + commandForImage + ')'
  imageDirectory = '/tmp/xcode_debug_images/'

  createDirectoryFormatStr = '[[NSFileManager defaultManager] createDirectoryAtPath:@"{}" withIntermediateDirectories:YES attributes:nil error:NULL]'
  createDirectoryCMD = createDirectoryFormatStr.format(imageDirectory)
  lldb.debugger.HandleCommand('expr (void) ' + createDirectoryCMD)

  imageName = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime()) + ".png"
  imagePath = imageDirectory + imageName
  createImageFormatStr = '[[NSFileManager defaultManager] createFileAtPath:@"{}" contents:(id)UIImagePNGRepresentation({}) attributes:nil]'
  createImageCMD = createImageFormatStr.format(imagePath, commandForImage)

  lldb.debugger.HandleCommand('expr (void) ' + createImageCMD)
  os.system('open ' + imagePath)

def _showLayer(layer):
  layer = '(' + layer + ')'

  lldb.debugger.HandleCommand('expr (void)UIGraphicsBeginImageContextWithOptions(((CGRect)[(id)' + layer + ' frame]).size, NO, 0)')
  lldb.debugger.HandleCommand('expr (void)[(id)' + layer + ' renderInContext:(void *)UIGraphicsGetCurrentContext()]')

  frame = lldb.debugger.GetSelectedTarget().GetProcess().GetSelectedThread().GetSelectedFrame()
  result = frame.EvaluateExpression('(UIImage *)UIGraphicsGetImageFromCurrentImageContext()')
  if result.GetError() is not None and str(result.GetError()) != 'success':
    print result.GetError()
  else:
    image = result.GetValue()
    _showImage(image)

  lldb.debugger.HandleCommand('expr (void)UIGraphicsEndImageContext()')


def _visualize(object):
  object = '(' + object + ')'
  
  if fb.evaluateBooleanExpression('(BOOL)((unsigned long)CFGetTypeID((CFTypeRef)' + object + ') == (unsigned long)CGImageGetTypeID())'):
    _showImage('(id)[UIImage imageWithCGImage:' + object + ']')
  else:
    comarisonStr = '(BOOL)[' + object + 'isKindOfClass:[{} class]]'
    if fb.evaluateBooleanExpression(comarisonStr.format('UIImage')):
      _showImage(object)
    elif fb.evaluateBooleanExpression(comarisonStr.format('UIView')):
      _showLayer('[(id)' + object + ' layer]')
    elif fb.evaluateBooleanExpression(comarisonStr.format('CALayer')):
      _showLayer(object)


class FBVisualizeCommand(fb.FBCommand):
  def name(self):
    return 'visualize'

  def description(self):
    return 'Open a UIImage, CGImageRef, UIView, or CALayer in Preview.app on your Mac.'

  def args(self):
    return [ fb.FBCommandArgument(arg='object', type='(id)', help='The object to visualize.') ]

  def run(self, arguments, options):
    _visualize(arguments[0])
