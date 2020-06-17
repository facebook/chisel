#!/usr/bin/python

# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import os
import sys

import fbchisellldbbase as fb
import fbchisellldbobjcruntimehelpers as runtimeHelpers
import fbchisellldbviewhelpers as viewHelpers
import lldb


def lldbcommands():
    return [FBFlickerViewCommand(), FBViewSearchCommand()]


class FBFlickerViewCommand(fb.FBCommand):
    def name(self):
        return "flicker"

    def description(self):
        return "Quickly show and hide a view to quickly help visualize where it is."

    def args(self):
        return [
            fb.FBCommandArgument(
                arg="viewOrLayer", type="UIView/NSView*", help="The view to flicker."
            )
        ]

    def run(self, arguments, options):
        object = fb.evaluateObjectExpression(arguments[0])

        isHidden = fb.evaluateBooleanExpression("[" + object + " isHidden]")
        shouldHide = not isHidden
        for _ in range(0, 2):
            viewHelpers.setViewHidden(object, shouldHide)
            viewHelpers.setViewHidden(object, isHidden)


class FBViewSearchCommand(fb.FBCommand):
    def name(self):
        return "vs"

    def description(self):
        return "Interactively search for a view by walking the hierarchy."

    def args(self):
        return [
            fb.FBCommandArgument(arg="view", type="UIView*", help="The view to border.")
        ]

    def run(self, arguments, options):
        print(
            "\nUse the following and (q) to quit.\n(w) move to superview\n(s) move to first subview\n(a) move to previous sibling\n(d) move to next sibling\n(p) print the hierarchy\n"
        )

        object = fb.evaluateInputExpression(arguments[0])
        walker = FlickerWalker(object)
        walker.run()


class FlickerWalker:
    def __init__(self, startView):
        self.setCurrentView(startView)

    def run(self):
        self.keepRunning = True
        initialAsync = lldb.debugger.GetAsync()
        # Needed so XCode doesn't hang if tap on Continue while lldb
        # is waiting for user input in 'vs' mode
        lldb.debugger.SetAsync(
            True
        )
        while self.keepRunning:
            charRead = sys.stdin.readline().rstrip("\n")
            self.inputCallback(charRead)
        else:
            lldb.debugger.SetAsync(initialAsync)

    def inputCallback(self, input):
        oldView = self.currentView

        if input == "q":
            cmd = 'echo %s | tr -d "\n" | pbcopy' % oldView
            os.system(cmd)

            print(
                "\nI hope "
                + oldView
                + " was what you were looking for. I put it on your clipboard."
            )
            viewHelpers.unmaskView(oldView)
            self.keepRunning = False

        elif input == "w":
            v = superviewOfView(self.currentView)
            if not v:
                print("There is no superview. Where are you trying to go?!")
            self.setCurrentView(v, oldView)
        elif input == "s":
            v = firstSubviewOfView(self.currentView)
            if not v:
                print("\nThe view has no subviews.\n")
            self.setCurrentView(v, oldView)
        elif input == "d":
            v = nthSiblingOfView(self.currentView, -1)
            if v == oldView:
                print("\nThere are no sibling views to this view.\n")
            self.setCurrentView(v, oldView)
        elif input == "a":
            v = nthSiblingOfView(self.currentView, 1)
            if v == oldView:
                print("\nThere are no sibling views to this view.\n")
            self.setCurrentView(v, oldView)
        elif input == "p":
            recursionName = "recursiveDescription"
            isMac = runtimeHelpers.isMacintoshArch()

            if isMac:
                recursionName = "_subtreeDescription"

            print(fb.describeObject("[(id){} {}]".format(oldView, recursionName)))
        else:
            print("\nI really have no idea what you meant by '" + input + "'... =\\\n")

    def setCurrentView(self, view, oldView=None):
        if view:
            self.currentView = view
            if oldView:
                viewHelpers.unmaskView(oldView)
            viewHelpers.maskView(self.currentView, "red", "0.4")
            print(fb.describeObject(view))


def superviewOfView(view):
    superview = fb.evaluateObjectExpression("[" + view + " superview]")
    if int(superview, 16) == 0:
        return None

    return superview


def subviewsOfView(view):
    return fb.evaluateObjectExpression("[" + view + " subviews]")


def firstSubviewOfView(view):
    subviews = subviewsOfView(view)
    numViews = fb.evaluateIntegerExpression("[(id)" + subviews + " count]")

    if numViews == 0:
        return None
    else:
        return fb.evaluateObjectExpression("[" + subviews + " objectAtIndex:0]")


def nthSiblingOfView(view, n):
    subviews = subviewsOfView(superviewOfView(view))
    numViews = fb.evaluateIntegerExpression("[(id)" + subviews + " count]")

    idx = fb.evaluateIntegerExpression(
        "[(id)" + subviews + " indexOfObject:" + view + "]"
    )

    newIdx = idx + n
    while newIdx < 0:
        newIdx += numViews
    newIdx = newIdx % numViews

    return fb.evaluateObjectExpression(
        "[(id)" + subviews + " objectAtIndex:" + str(newIdx) + "]"
    )
