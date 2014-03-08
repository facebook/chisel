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

def lldbcommands():
  return [
    FBShowImageCommand(),
    FBShowImageRefCommand(),
    FBShowViewCommand(),
    FBShowLayerCommand(),
  ]

def _showLocalImage(commandForImage, imageDirectory, imagePath):
  commandForImage = '(' + commandForImage + ')'

  createDirectoryFormatStr = '[[NSFileManager defaultManager] createDirectoryAtPath:@"{}" withIntermediateDirectories:YES attributes:nil error:NULL]'
  createDirectoryCMD = createDirectoryFormatStr.format(imageDirectory)
  lldb.debugger.HandleCommand('expr (void) ' + createDirectoryCMD)

  createImageFormatStr = '[[NSFileManager defaultManager] createFileAtPath:@"{}" contents:(id)UIImagePNGRepresentation({}) attributes:nil]'
  createImageCMD = createImageFormatStr.format(imagePath, commandForImage)

  lldb.debugger.HandleCommand('expr (void) ' + createImageCMD)
  os.system('open ' + imagePath)


def _showRemoteImage(commandForImage, imageDirectory, imagePath):
  commandForImage = '(' + commandForImage + ')'

  try:
    os.makedirs(imageDirectory)
  except OSError as e:
    if e.errno == errno.EEXIST and os.path.isdir(imageDirectory):
      pass
    else:
      raise

  imageDataAddress = fb.evaluateExpression('(id)UIImagePNGRepresentation(' + commandForImage +')')
  imageBytesStartAddress = fb.evaluateExpression('(void *)[(id)' + imageDataAddress + ' bytes]')
  imageBytesLength = fb.evaluateExpression('(NSUInteger)[(id)' + imageDataAddress + ' length]')

  address = int(imageBytesStartAddress,16)
  length = int(imageBytesLength)

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


def _showImage(commandForImage):
  imageDirectory = '/tmp/xcode_debug_images/'

  imageName = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime()) + ".png"
  imagePath = imageDirectory + imageName

  device = fb.evaluateExpressionValue('(id) [[[UIDevice currentDevice] model] lowercaseString]')
  if 'simulator' in device.GetObjectDescription():
    _showLocalImage(commandForImage, imageDirectory, imagePath)
  else:
    _showRemoteImage(commandForImage, imageDirectory, imagePath)


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


class FBShowImageCommand(fb.FBCommand):
  def name(self):
    return 'showimage'

  def description(self):
    return 'Open a UIImage in Preview.app on your Mac.'

  def args(self):
    return [ fb.FBCommandArgument(arg='anImage', type='UIImage*', help='The image to examine.') ]

  def run(self, arguments, options):
    _showImage(arguments[0])


class FBShowImageRefCommand(fb.FBCommand):
  def name(self):
    return 'showimageref'

  def description(self):
    return 'Open a CGImageRef in Preview.app on your Mac.'

  def args(self):
    return [ fb.FBCommandArgument(arg='anImageRef', type='CGImageRef', help='The image to examine.') ]

  def run(self, arguments, options):
    _showImage('(id)[UIImage imageWithCGImage:' + arguments[0] + ']')


class FBShowViewCommand(fb.FBCommand):
  def name(self):
    return 'showview'

  def description(self):
    return 'Render the given UIView into an image and open it in Preview.app on your Mac.'

  def args(self):
    return [ fb.FBCommandArgument(arg='aView', type='UIView*', help='The view to examine.') ]

  def run(self, arguments, options):
    _showLayer('[(id)' + arguments[0] + ' layer]')


class FBShowLayerCommand(fb.FBCommand):
  def name(self):
    return 'showlayer'

  def description(self):
    return 'Render the given CALayer into an image and open it in Preview.app on your Mac.'

  def args(self):
    return [ fb.FBCommandArgument(arg='aLayer', type='CALayer*', help='The layer to examine.') ]

  def run(self, arguments, options):
    _showLayer(arguments[0])

