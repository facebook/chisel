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
import errno
import fblldbbase as fb
import fblldbobjecthelpers as objectHelpers

def lldbcommands():
  return [
    FBVisualizeCommand()
  ]

def _showImage(commandForImage):
  imageDirectory = '/tmp/xcode_debug_images/'

  imageName = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime()) + ".png"
  imagePath = imageDirectory + imageName

  try:
    os.makedirs(imageDirectory)
  except OSError as e:
    if e.errno == errno.EEXIST and os.path.isdir(imageDirectory):
      pass
    else:
      raise

  imageDataAddress = fb.evaluateObjectExpression('UIImagePNGRepresentation((id)' + commandForImage + ')')
  imageBytesStartAddress = fb.evaluateExpression('(void *)[(id)' + imageDataAddress + ' bytes]')
  imageBytesLength = fb.evaluateExpression('(NSUInteger)[(id)' + imageDataAddress + ' length]')

  address = int(imageBytesStartAddress, 16)
  length = int(imageBytesLength)

  if not (address or length):
    print 'Could not get image data.'
    return

  process = lldb.debugger.GetSelectedTarget().GetProcess()
  error = lldb.SBError()
  mem = process.ReadMemory(address, length, error)

  if error is not None and str(error) != 'success':
    print error
  else:
    imgFile = open(imagePath, 'wb')
    imgFile.write(mem)
    imgFile.close()
    os.system('open ' + imagePath)

def _showLayer(layer):
  layer = '(' + layer + ')'

  lldb.debugger.HandleCommand('expr -l objc++ -- (void)UIGraphicsBeginImageContextWithOptions(((CGRect)[(id)' + layer + ' bounds]).size, NO, 0.0)')
  lldb.debugger.HandleCommand('expr -l objc++ -- (void)[(id)' + layer + ' renderInContext:(void *)UIGraphicsGetCurrentContext()]')

  frame = lldb.debugger.GetSelectedTarget().GetProcess().GetSelectedThread().GetSelectedFrame()
  result = frame.EvaluateExpression('(UIImage *)UIGraphicsGetImageFromCurrentImageContext()')
  if result.GetError() is not None and str(result.GetError()) != 'success':
    print result.GetError()
  else:
    image = result.GetValue()
    _showImage(image)

  lldb.debugger.HandleCommand('expr -l objc++ -- (void)UIGraphicsEndImageContext()')

def _dataIsImage(data):
  data = '(' + data + ')'

  frame = lldb.debugger.GetSelectedTarget().GetProcess().GetSelectedThread().GetSelectedFrame()
  result = frame.EvaluateExpression('(id)[UIImage imageWithData:' + data + ']')

  if result.GetError() is not None and str(result.GetError()) != 'success':
    return 0
  else:
    isImage = result.GetValueAsUnsigned() != 0
    if isImage:
      return 1
    else:
      return 0

def _dataIsString(data):
  data = '(' + data + ')'

  frame = lldb.debugger.GetSelectedTarget().GetProcess().GetSelectedThread().GetSelectedFrame()
  result = frame.EvaluateExpression('(NSString*)[[NSString alloc] initWithData:' + data + ' encoding:4]')

  if result.GetError() is not None and str(result.GetError()) != 'success':
    return 0
  else:
    isString = result.GetValueAsUnsigned() != 0
    if isString:
      return 1
    else:
      return 0

def _visualize(target):
  target = '(' + target + ')'

  if fb.evaluateBooleanExpression('(unsigned long)CFGetTypeID((CFTypeRef)' + target + ') == (unsigned long)CGImageGetTypeID()'):
    _showImage('(id)[UIImage imageWithCGImage:' + target + ']')
  else:
    if objectHelpers.isKindOfClass(target, 'UIImage'):
      _showImage(target)
    elif objectHelpers.isKindOfClass(target, 'UIView'):
      _showLayer('[(id)' + target + ' layer]')
    elif objectHelpers.isKindOfClass(target, 'CALayer'):
      _showLayer(target)
    elif objectHelpers.isKindOfClass(target, 'NSData'):
      if _dataIsImage(target):
        _showImage('(id)[UIImage imageWithData:' + target + ']')
      elif _dataIsString(target):
        lldb.debugger.HandleCommand('expr -O -l objc++ -- (NSString*)[[NSString alloc] initWithData:' + target + ' encoding:4]')
      else:
        print 'Data isn\'t an image and isn\'t a string.'
    else:
      print '{} isn\'t supported. You can visualize UIImage, CGImageRef, UIView, CALayer or NSData.'.format(objectHelpers.className(target))

class FBVisualizeCommand(fb.FBCommand):
  def name(self):
    return 'visualize'

  def description(self):
    return 'Open a UIImage, CGImageRef, UIView, or CALayer in Preview.app on your Mac.'

  def args(self):
    return [ fb.FBCommandArgument(arg='target', type='(id)', help='The object to visualize.') ]

  def run(self, arguments, options):
    _visualize(arguments[0])
