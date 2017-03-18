#!/usr/bin/python

import os

import lldb
import fblldbbase as fb

def lldbcommands():
  return [ PrintKeyWindowLevel() ]

class PrintKeyWindowLevel(fb.FBCommand):
  def name(self):
    return 'osand'

  def description(self):
    return 'Open the Simulator sandbox folder of the app in Finder'

  def run(self, arguments, options):
  	homeDirectory = fb.evaluateExpressionValue('(NSString*)NSHomeDirectory()').GetObjectDescription()
  	print 'the home directory:' + homeDirectory
  	os.system('open ' + homeDirectory)

    