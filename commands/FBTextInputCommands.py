#!/usr/bin/python

# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import fbchisellldbbase as fb
import fbchisellldbviewhelpers as viewHelpers


ACCESSIBILITY_ID = 0
REPLACEMENT_TEXT = 1
INPUT_TEXT = 0


def lldbcommands():
    return [FBInputTexByAccessibilityIdCommand(), FBInputTexToFirstResponderCommand()]


class FBInputTexByAccessibilityIdCommand(fb.FBCommand):
    def name(self):
        return "settext"

    def description(self):
        return "Set text on text on a view by accessibility id."

    def args(self):
        return [
            fb.FBCommandArgument(
                arg="accessibilityId",
                type="string",
                help="The accessibility ID of the input view.",
            ),
            fb.FBCommandArgument(
                arg="replacementText", type="string", help="The text to set."
            ),
        ]

    def run(self, arguments, options):
        self.findView(
            rootView(), arguments[ACCESSIBILITY_ID], arguments[REPLACEMENT_TEXT]
        )

    def findView(self, view, searchIdentifier, replacementText):
        views = subviewsOfView(view)
        for index in range(0, viewsCount(views)):
            subview = subviewAtIndex(views, index)
            self.findView(subview, searchIdentifier, replacementText)
        else:
            identifier = accessibilityIdentifier(view)
            if isEqualToString(identifier, searchIdentifier):
                setTextInView(view, replacementText)


class FBInputTexToFirstResponderCommand(fb.FBCommand):
    def name(self):
        return "setinput"

    def description(self):
        return "Input text into text field or text view that is first responder."

    def args(self):
        return [
            fb.FBCommandArgument(
                arg="inputText", type="string", help="The text to input."
            )
        ]

    def run(self, arguments, options):
        self.findFirstResponder(rootView(), arguments[INPUT_TEXT])

    def findFirstResponder(self, view, replacementText):
        views = subviewsOfView(view)
        if isFirstResponder(view):
            setTextInView(view, replacementText)
        else:
            for index in range(0, viewsCount(views)):
                subview = subviewAtIndex(views, index)
                self.findFirstResponder(subview, replacementText)


# Some helpers
def rootView():
    return fb.evaluateObjectExpression("[[UIApplication sharedApplication] keyWindow]")


def subviewsOfView(view):
    return fb.evaluateObjectExpression("[%s subviews]" % view)


def subviewAtIndex(views, index):
    return fb.evaluateObjectExpression("[%s objectAtIndex:%i]" % (views, index))


def viewsCount(views):
    return int(fb.evaluateExpression("(int)[%s count]" % views))


def accessibilityIdentifier(view):
    return fb.evaluateObjectExpression("[%s accessibilityIdentifier]" % view)


def isEqualToString(identifier, needle):
    return fb.evaluateBooleanExpression(
        '[%s isEqualToString:@"%s"]' % (identifier, needle)
    )


def setTextInView(view, text):
    fb.evaluateObjectExpression('[%s setText:@"%s"]' % (view, text))
    viewHelpers.flushCoreAnimationTransaction()


def isFirstResponder(view):
    return fb.evaluateBooleanExpression("[%s isFirstResponder]" % view)
