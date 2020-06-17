#!/usr/bin/python

# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import os
import re

import fbchisellldbbase as fb
import fbchisellldbobjcruntimehelpers as objc
import fbchisellldbviewcontrollerhelpers as vcHelpers
import lldb


def lldbcommands():
    return [FBFindViewControllerCommand(), FBFindViewCommand(), FBTapLoggerCommand()]


class FBFindViewControllerCommand(fb.FBCommand):
    def name(self):
        return "fvc"

    def description(self):
        return "Find the view controllers whose class names match classNameRegex and puts the address of first on the clipboard."

    def options(self):
        return [
            fb.FBCommandArgument(
                short="-n",
                long="--name",
                arg="classNameRegex",
                type="string",
                help="The view-controller-class regex to search the view controller hierarchy for.",
            ),
            fb.FBCommandArgument(
                short="-v",
                long="--view",
                arg="view",
                type="UIView",
                help="This function will print the View Controller that owns this view.",
            ),
        ]

    def run(self, arguments, options):
        if options.classNameRegex and options.view:
            print("Do not set both the --name and --view flags")
        elif options.view:
            self.findOwningViewController(options.view)
        else:
            output = vcHelpers.viewControllerRecursiveDescription(
                "(id)[[[UIApplication sharedApplication] keyWindow] rootViewController]"
            )
            searchString = (
                options.classNameRegex if options.classNameRegex else arguments[0]
            )
            printMatchesInViewOutputStringAndCopyFirstToClipboard(searchString, output)

    def findOwningViewController(self, object):
        while object:
            if self.isViewController(object):
                description = fb.evaluateExpressionValue(object).GetObjectDescription()
                print("Found the owning view controller.\n{}".format(description))
                cmd = 'echo {} | tr -d "\n" | pbcopy'.format(object)
                os.system(cmd)
                return
            else:
                object = self.nextResponder(object)
        print("Could not find an owning view controller")

    @staticmethod
    def isViewController(object):
        command = "[(id){} isKindOfClass:[UIViewController class]]".format(object)
        isVC = fb.evaluateBooleanExpression(command)
        return isVC

    @staticmethod
    def nextResponder(object):
        command = "[((id){}) nextResponder]".format(object)
        nextResponder = fb.evaluateObjectExpression(command)
        try:
            if int(nextResponder, 0):
                return nextResponder
            else:
                return None
        except Exception:
            return None


class FBFindViewCommand(fb.FBCommand):
    def name(self):
        return "fv"

    def description(self):
        return "Find the views whose class names match classNameRegex and puts the address of first on the clipboard."

    def args(self):
        return [
            fb.FBCommandArgument(
                arg="classNameRegex",
                type="string",
                help="The view-class regex to search the view hierarchy for.",
            )
        ]

    def run(self, arguments, options):
        output = fb.evaluateExpressionValue(
            "(id)[[[UIApplication sharedApplication] keyWindow] recursiveDescription]"
        ).GetObjectDescription()
        printMatchesInViewOutputStringAndCopyFirstToClipboard(arguments[0], output)


def printMatchesInViewOutputStringAndCopyFirstToClipboard(needle, haystack):
    first = None
    for match in re.finditer(
        ".*<.*(" + needle + ")\\S*: (0x[0-9a-fA-F]*);.*", haystack, re.IGNORECASE
    ):
        view = match.groups()[-1]
        className = fb.evaluateExpressionValue(
            "(id)[(" + view + ") class]"
        ).GetObjectDescription()
        print("{} {}".format(view, className))
        if first is None:
            first = view
            cmd = 'echo %s | tr -d "\n" | pbcopy' % view
            os.system(cmd)


class FBTapLoggerCommand(fb.FBCommand):
    def name(self):
        return "taplog"

    def description(self):
        return "Log tapped view to the console."

    def run(self, arguments, options):
        parameterExpr = objc.functionPreambleExpressionForObjectParameterAtIndex(0)
        breakpoint = lldb.debugger.GetSelectedTarget().BreakpointCreateByName(
            "-[UIApplication sendEvent:]"
        )
        breakpoint.SetCondition(
            "(int)["
            + parameterExpr
            + " type] == 0 && (int)[[["
            + parameterExpr
            + " allTouches] anyObject] phase] == 0"
        )
        breakpoint.SetOneShot(True)
        lldb.debugger.HandleCommand(
            "breakpoint command add -s python -F \"sys.modules['"
            + __name__
            + "']."
            + self.__class__.__name__
            + '.taplog_callback" '
            + str(breakpoint.id)
        )
        lldb.debugger.SetAsync(True)
        lldb.debugger.HandleCommand("continue")

    @staticmethod
    def taplog_callback(frame, bp_loc, internal_dict):
        parameterExpr = objc.functionPreambleExpressionForObjectParameterAtIndex(0)
        print(
            "Gesture Recognizers:\n{}".format(
                fb.describeObject(
                    "[[[%s allTouches] anyObject] gestureRecognizers]" % (parameterExpr)
                )
            )
        )
        print(
            "View:\n{}".format(
                fb.describeObject(
                    "[[[%s allTouches] anyObject] view]" % (parameterExpr)
                )
            )
        )
        # We don't want to proceed event (click on button for example), so we just skip it
        lldb.debugger.HandleCommand("thread return")
