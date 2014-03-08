#!/usr/bin/python
# Example file with custom commands, located at /magical/commands/example.py

import os
import re

import lldb
import fblldbbase as fb
import fblldbviewcontrollerhelpers as vcHelpers

def lldbcommands():
  return [
    GAPrintDataAsStringCommand(),
  ]

class GAPrintDataAsStringCommand(fb.FBCommand):
  def name(self):
    return 'pds'

  def description(self):
    return 'print NSData as UTF8 string'

  def args(self):
    return [ fb.FBCommandArgument(arg='data', type='NSData*', help='The data you want to see as string.') ]

  def run(self, arguments, options):
    lldb.debugger.HandleCommand('po (NSString*)[[NSString alloc] initWithData:' + arguments[0] + ' encoding:4]')