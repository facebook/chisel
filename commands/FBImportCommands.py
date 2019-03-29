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
    ImportUIKitModule()
  ]
  
class ImportUIKitModule(fb.FBCommand):
  def name(self):
    return 'uikit'
    
  def description(self):
    return 'Imports the UIKit module to get access to the types while in lldb.'
    
  def run(self, arguments, options):
    frame = lldb.debugger.GetSelectedTarget().GetProcess().GetSelectedThread().GetSelectedFrame()
    fb.importModule(frame, 'UIKit')
    
