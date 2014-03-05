#!/usr/bin/python

# Copyright (c) 2014, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

import os
import re

import lldb
import fblldbbase as fb
import fblldbviewcontrollerhelpers as vcHelpers

def lldbcommands():
  return [
    FBFindViewControllerCommand(),
    FBFindViewCommand(),
    FBFindViewByAccessibilityLabelCommand(),
  ]

class FBFindViewControllerCommand(fb.FBCommand):
  def name(self):
    return 'fvc'

  def description(self):
    return 'Find the view controllers whose class names match classNameRegex and puts the address of first on the clipboard.'

  def args(self):
    return [ fb.FBCommandArgument(arg='classNameRegex', type='string', help='The view-controller-class regex to search the view controller hierarchy for.') ]

  def run(self, arguments, options):
    output = vcHelpers.viewControllerRecursiveDescription('(id)[[UIWindow keyWindow] rootViewController]')
    printMatchesInViewOutputStringAndCopyFirstToClipboard(arguments[0], output)


class FBFindViewCommand(fb.FBCommand):
  def name(self):
    return 'fv'

  def description(self):
      return 'Find the views whose class names match classNameRegex and puts the address of first on the clipboard.'

  def args(self):
    return [ fb.FBCommandArgument(arg='classNameRegex', type='string', help='The view-class regex to search the view hierarchy for.') ]

  def run(self, arguments, options):
    output = fb.evaluateExpressionValue('(id)[[UIWindow keyWindow] recursiveDescription]').GetObjectDescription()
    printMatchesInViewOutputStringAndCopyFirstToClipboard(arguments[0], output)


def printMatchesInViewOutputStringAndCopyFirstToClipboard(needle, haystack):
  matches = re.findall('.*<.*' + needle + '.*: (0x[0-9a-fA-F]*);.*', haystack, re.IGNORECASE)
  for match in matches:
    className = fb.evaluateExpressionValue('(id)[(' + match + ') class]').GetObjectDescription()
    print('{} {}'.format(match, className))

  if len(matches) > 0:
    cmd = 'echo %s | tr -d "\n" | pbcopy' % matches[0]
    os.system(cmd)


class FBFindViewByAccessibilityLabelCommand(fb.FBCommand):
  def name(self):
    return 'fa11y'

  def description(self):
      return 'Find the views whose accessibility labels match labelRegex and puts the address of the first result on the clipboard.'

  def args(self):
    return [ fb.FBCommandArgument(arg='labelRegex', type='string', help='The accessibility label regex to search the view hierarchy for.') ]

  def run(self, arguments, options):
    first = None
    haystack = fb.evaluateExpressionValue('(id)[[UIWindow keyWindow] recursiveDescription]').GetObjectDescription()
    needle = arguments[0]

    allViews = re.findall('.* (0x[0-9a-fA-F]*);.*', haystack)
    for view in allViews:
      a11yLabel = fb.evaluateExpressionValue('(id)[(' + view + ') accessibilityLabel]').GetObjectDescription()
      if re.match(r'.*' + needle + '.*', a11yLabel, re.IGNORECASE):
        print('{} {}'.format(view, a11yLabel))

        if first == None:
          first = view
          cmd = 'echo %s | tr -d "\n" | pbcopy' % first
          os.system(cmd)
