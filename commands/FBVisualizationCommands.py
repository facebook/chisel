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

  toPNG = '(id)UIImagePNGRepresentation((id){})'.format(commandForImage)
  imageDataAddress = fb.evaluateExpressionValue(toPNG, tryAllThreads=True).GetValue()
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

def _colorIsCGColorRef(color):
  color = '(CGColorRef)(' + color + ')'

  result = fb.evaluateExpressionValue('(unsigned long)CFGetTypeID({color}) == (unsigned long)CGColorGetTypeID()'.format(color=color))

  if result.GetError() is not None and str(result.GetError()) != 'success':
    print "got error: {}".format(result)
    return False
  else:
    isCFColor = result.GetValueAsUnsigned() != 0
    return isCFColor

def _showColor(color):
    color = '(' + color + ')'

    colorToUse = color
    isCF = _colorIsCGColorRef(color)
    if isCF:
      colorToUse = '[[UIColor alloc] initWithCGColor:(CGColorRef){}]'.format(color)
    else:
      isCI = objectHelpers.isKindOfClass(color, 'CIColor')
      if isCI:
        colorToUse = '[UIColor colorWithCIColor:(CIColor *){}]'.format(color)

    imageSize = 58
    fb.evaluateEffect('UIGraphicsBeginImageContextWithOptions((CGSize)CGSizeMake({imageSize}, {imageSize}), NO, 0.0)'.format(imageSize=imageSize))
    fb.evaluateEffect('[(id){} setFill]'.format(colorToUse))
    fb.evaluateEffect('UIRectFill((CGRect)CGRectMake(0.0, 0.0, {imageSize}, {imageSize}))'.format(imageSize=imageSize))

    result = fb.evaluateExpressionValue('(UIImage *)UIGraphicsGetImageFromCurrentImageContext()')
    if result.GetError() is not None and str(result.GetError()) != 'success':
      print "got error {}".format(result)
      print result.GetError()
    else:
      image = result.GetValue()
      _showImage(image)

    fb.evaluateEffect('UIGraphicsEndImageContext()')

def _showLayer(layer):
  layer = '(' + layer + ')'
  size = '((CGRect)[(id)' + layer + ' bounds]).size'

  width = float(fb.evaluateExpression('(CGFloat)(' + size + '.width)'))
  height = float(fb.evaluateExpression('(CGFloat)(' + size + '.height)'))
  if width == 0.0 or height == 0.0:
    print 'Nothing to see here - the size of this element is {} x {}.'.format(width, height)
    return

  fb.evaluateEffect('UIGraphicsBeginImageContextWithOptions(' + size + ', NO, 0.0)')
  fb.evaluateEffect('[(id)' + layer + ' renderInContext:(void *)UIGraphicsGetCurrentContext()]')

  result = fb.evaluateExpressionValue('(UIImage *)UIGraphicsGetImageFromCurrentImageContext()')
  if result.GetError() is not None and str(result.GetError()) != 'success':
    print result.GetError()
  else:
    image = result.GetValue()
    _showImage(image)

  fb.evaluateEffect('UIGraphicsEndImageContext()')

def _dataIsImage(data):
  data = '(' + data + ')'

  result = fb.evaluateExpressionValue('(id)[UIImage imageWithData:' + data + ']')

  if result.GetError() is not None and str(result.GetError()) != 'success':
    return False
  else:
    isImage = result.GetValueAsUnsigned() != 0
    return isImage

def _dataIsString(data):
  data = '(' + data + ')'

  result = fb.evaluateExpressionValue('(NSString*)[[NSString alloc] initWithData:' + data + ' encoding:4]')

  if result.GetError() is not None and str(result.GetError()) != 'success':
    return False
  else:
    isString = result.GetValueAsUnsigned() != 0
    return isString

def _visualize(target):
  target = fb.evaluateInputExpression(target)

  if fb.evaluateBooleanExpression('(unsigned long)CFGetTypeID((CFTypeRef)' + target + ') == (unsigned long)CGImageGetTypeID()'):
    _showImage('(id)[UIImage imageWithCGImage:' + target + ']')
  else:
    if objectHelpers.isKindOfClass(target, 'UIImage'):
      _showImage(target)
    elif objectHelpers.isKindOfClass(target, 'UIView'):
      _showLayer('[(id)' + target + ' layer]')
    elif objectHelpers.isKindOfClass(target, 'CALayer'):
      _showLayer(target)
    elif objectHelpers.isKindOfClass(target, 'UIColor') or objectHelpers.isKindOfClass(target, 'CIColor') or _colorIsCGColorRef(target):
      _showColor(target)
    elif objectHelpers.isKindOfClass(target, 'NSData'):
      if _dataIsImage(target):
        _showImage('(id)[UIImage imageWithData:' + target + ']')
      elif _dataIsString(target):
        print fb.describeObject('[[NSString alloc] initWithData:' + target + ' encoding:4]')
      else:
        print 'Data isn\'t an image and isn\'t a string.'
    else:
      print '{} isn\'t supported. You can visualize UIImage, CGImageRef, UIView, CALayer, NSData, UIColor, CIColor, or CGColorRef.'.format(objectHelpers.className(target))

class FBVisualizeCommand(fb.FBCommand):
  def name(self):
    return 'visualize'

  def description(self):
    return 'Open a UIImage, CGImageRef, UIView, or CALayer in Preview.app on your Mac.'

  def args(self):
    return [ fb.FBCommandArgument(arg='target', type='(id)', help='The object to visualize.') ]

  def run(self, arguments, options):
    _visualize(arguments[0])
