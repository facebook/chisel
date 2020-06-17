#!/usr/bin/python

# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import fbchisellldbbase as fb
import fbchisellldbobjcruntimehelpers as runtimeHelpers


def flushCoreAnimationTransaction():
    fb.evaluateEffect("[CATransaction flush]")


def setViewHidden(object, hidden):
    fb.evaluateEffect("[{} setHidden:{}]".format(object, int(hidden)))
    flushCoreAnimationTransaction()


def maskView(viewOrLayer, color, alpha):
    unmaskView(viewOrLayer)
    window = fb.evaluateExpression(
        "(UIWindow *)[[UIApplication sharedApplication] keyWindow]"
    )
    origin = convertPoint(0, 0, viewOrLayer, window)
    size = fb.evaluateExpressionValue(
        "(CGSize)((CGRect)[(id)%s frame]).size" % viewOrLayer
    )

    rectExpr = "(CGRect){{%s, %s}, {%s, %s}}" % (
        origin.GetChildMemberWithName("x").GetValue(),
        origin.GetChildMemberWithName("y").GetValue(),
        size.GetChildMemberWithName("width").GetValue(),
        size.GetChildMemberWithName("height").GetValue(),
    )
    mask = fb.evaluateExpression("(id)[[UIView alloc] initWithFrame:%s]" % rectExpr)

    fb.evaluateEffect("[%s setTag:(NSInteger)%s]" % (mask, viewOrLayer))
    fb.evaluateEffect("[%s setBackgroundColor:[UIColor %sColor]]" % (mask, color))
    fb.evaluateEffect("[%s setAlpha:(CGFloat)%s]" % (mask, alpha))
    fb.evaluateEffect("[%s addSubview:%s]" % (window, mask))
    flushCoreAnimationTransaction()


def unmaskView(viewOrLayer):
    window = fb.evaluateExpression(
        "(UIWindow *)[[UIApplication sharedApplication] keyWindow]"
    )
    mask = fb.evaluateExpression(
        "(UIView *)[%s viewWithTag:(NSInteger)%s]" % (window, viewOrLayer)
    )
    fb.evaluateEffect("[%s removeFromSuperview]" % mask)
    flushCoreAnimationTransaction()


def convertPoint(x, y, fromViewOrLayer, toViewOrLayer):
    fromLayer = convertToLayer(fromViewOrLayer)
    toLayer = convertToLayer(toViewOrLayer)
    return fb.evaluateExpressionValue(
        "(CGPoint)[%s convertPoint:(CGPoint){ .x = %s, .y = %s } toLayer:(CALayer *)%s]"
        % (fromLayer, x, y, toLayer)
    )


def convertToLayer(viewOrLayer):
    if fb.evaluateBooleanExpression(
        "[(id)%s isKindOfClass:(Class)[CALayer class]]" % viewOrLayer
    ):
        return viewOrLayer
    elif fb.evaluateBooleanExpression(
        "[(id)%s respondsToSelector:(SEL)@selector(layer)]" % viewOrLayer
    ):
        return fb.evaluateExpression("(CALayer *)[%s layer]" % viewOrLayer)
    else:
        raise Exception("Argument must be a CALayer, UIView, or NSView.")


def isUIView(obj):
    return not runtimeHelpers.isMacintoshArch() and fb.evaluateBooleanExpression(
        "[(id)%s isKindOfClass:(Class)[UIView class]]" % obj
    )


def isNSView(obj):
    return runtimeHelpers.isMacintoshArch() and fb.evaluateBooleanExpression(
        "[(id)%s isKindOfClass:(Class)[NSView class]]" % obj
    )


def isView(obj):
    return isUIView(obj) or isNSView(obj)


# Generates a BFS of the views tree starting at the given view as root.
# Yields a tuple of the current view in the tree and its level (view, level)
def subviewsOfView(view):
    views = [(view, 0)]
    yield views[0]
    while views:
        (view, level) = views.pop(0)
        subviews = fb.evaluateExpression("(id)[%s subviews]" % view)
        subviewsCount = int(fb.evaluateExpression("(int)[(id)%s count]" % subviews))
        for i in range(subviewsCount):
            subview = fb.evaluateExpression("(id)[%s objectAtIndex:%i]" % (subviews, i))
            views.append((subview, level + 1))
            yield (subview, level + 1)


def upwardsRecursiveDescription(view, maxDepth=0):
    if not fb.evaluateBooleanExpression(
        "[(id)%s isKindOfClass:(Class)[UIView class]]" % view
    ) and not fb.evaluateBooleanExpression(
        "[(id)%s isKindOfClass:(Class)[NSView class]]" % view
    ):
        return None

    currentView = view
    recursiveDescription = []
    depth = 0

    while currentView and (maxDepth <= 0 or depth <= maxDepth):
        depth += 1

        viewDescription = fb.evaluateExpressionValue(
            "(id)[%s debugDescription]" % (currentView)
        ).GetObjectDescription()
        currentView = fb.evaluateExpression("(void*)[%s superview]" % (currentView))
        try:
            if int(currentView, 0) == 0:
                currentView = None
        except Exception:
            currentView = None

        if viewDescription:
            recursiveDescription.insert(0, viewDescription)

    if not len(viewDescription):
        return None

    currentPrefix = ""
    builder = ""
    for viewDescription in recursiveDescription:
        builder += currentPrefix + viewDescription + "\n"
        currentPrefix += "   | "

    return builder


def slowAnimation(speed=1):
    fb.evaluateEffect(
        '[[[UIApplication sharedApplication] windows] setValue:@(%s) forKeyPath:@"layer.speed"]'
        % speed
    )
