#!/usr/bin/python

# Copyright (c) 2014, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.


import lldb
import fblldbbase as fb

def lldbcommands():
  return [
    FBPrintAutolayoutTrace(),
  ]

class FBPrintAutolayoutTrace(fb.FBCommand):
  def name(self):
    return 'paltrace'

  def description(self):
    return "Print the Auto Layout trace for the given view. Defaults to the key window."

  def args(self):
    return [ fb.FBCommandArgument(arg='view', type='UIView *', help='The view to print the Auto Layout trace for.', default='(id)[[UIApplication sharedApplication] keyWindow]') ]

  def run(self, arguments, options):
    lldb.debugger.HandleCommand('po (id)[{} _autolayoutTrace]'.format(arguments[0]))
