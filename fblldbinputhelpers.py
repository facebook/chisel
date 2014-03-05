#!/usr/bin/python

# Copyright (c) 2014, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

import lldb

class FBInputHandler:
  def __init__(self, debugger, callback):
    self.debugger = debugger
    self.callback = callback
    self.inputReader = lldb.SBInputReader()
    self.inputReader.Initialize(
                                debugger,
                                self.handleInput,
                                lldb.eInputReaderGranularityLine,
                                None,
                                None, # prompt
                                True # echo
                                )

  def isValid(self):
    return not self.inputReader.IsDone()

  def start(self):
    self.debugger.PushInputReader(self.inputReader)

  def stop(self):
    self.inputReader.SetIsDone(True)

  def handleInput(self, inputReader, notification, bytes):
    if (notification == lldb.eInputReaderGotToken):
      self.callback(bytes)
    elif (notification == lldb.eInputReaderInterrupt):
      self.stop()
    
    return len(bytes)
