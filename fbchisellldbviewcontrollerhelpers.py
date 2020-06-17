#!/usr/bin/python

# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import fbchisellldbbase as fb
import fbchisellldbobjcruntimehelpers as runtimeHelpers


def presentViewController(viewController):
    vc = "(%s)" % (viewController)

    if fb.evaluateBooleanExpression(
        "%s != nil && ((BOOL)[(id)%s isKindOfClass:(Class)[UIViewController class]])"
        % (vc, vc)
    ):
        notPresented = fb.evaluateBooleanExpression(
            "[%s presentingViewController] == nil" % vc
        )

        if notPresented:
            fb.evaluateEffect(
                "[[[[UIApplication sharedApplication] keyWindow] rootViewController] presentViewController:%s animated:YES completion:nil]"
                % vc
            )
        else:
            raise Exception("Argument is already presented")
    else:
        raise Exception("Argument must be a UIViewController")


def dismissViewController(viewController):
    vc = "(%s)" % (viewController)

    if fb.evaluateBooleanExpression(
        "%s != nil && ((BOOL)[(id)%s isKindOfClass:(Class)[UIViewController class]])"
        % (vc, vc)
    ):
        isPresented = fb.evaluateBooleanExpression(
            "[%s presentingViewController] != nil" % vc
        )

        if isPresented:
            fb.evaluateEffect(
                "[(UIViewController *)%s dismissViewControllerAnimated:YES completion:nil]"
                % vc
            )
        else:
            raise Exception("Argument must be presented")
    else:
        raise Exception("Argument must be a UIViewController")


def viewControllerRecursiveDescription(vc):
    return _recursiveViewControllerDescriptionWithPrefixAndChildPrefix(
        fb.evaluateObjectExpression(vc), "", "", ""
    )


def _viewControllerDescription(viewController):
    vc = "(%s)" % (viewController)

    if fb.evaluateBooleanExpression("[(id)%s isViewLoaded]" % (vc)):
        result = fb.evaluateExpressionValue(
            '(id)[[NSString alloc] initWithFormat:@"<%%@: %%p; view = <%%@; %%p>; frame = (%%g, %%g; %%g, %%g)>", (id)NSStringFromClass((id)[(id)%s class]), %s, (id)[(id)[(id)%s view] class], (id)[(id)%s view], ((CGRect)[(id)[(id)%s view] frame]).origin.x, ((CGRect)[(id)[(id)%s view] frame]).origin.y, ((CGRect)[(id)[(id)%s view] frame]).size.width, ((CGRect)[(id)[(id)%s view] frame]).size.height]'
            % (vc, vc, vc, vc, vc, vc, vc, vc)
        )
    else:
        result = fb.evaluateExpressionValue(
            '(id)[[NSString alloc] initWithFormat:@"<%%@: %%p; view not loaded>", (id)NSStringFromClass((id)[(id)%s class]), %s]'
            % (vc, vc)
        )

    if result.GetError() is not None and str(result.GetError()) != "success":
        return "[Error getting description.]"
    else:
        return result.GetObjectDescription()


def _recursiveViewControllerDescriptionWithPrefixAndChildPrefix(
    vc, string, prefix, childPrefix
):
    isMac = runtimeHelpers.isMacintoshArch()

    s = "%s%s%s\n" % (
        prefix,
        "" if prefix == "" else " ",
        _viewControllerDescription(vc),
    )

    nextPrefix = childPrefix + "   |"

    numChildViewControllers = fb.evaluateIntegerExpression(
        "(int)[(id)[%s childViewControllers] count]" % (vc)
    )

    for i in range(0, numChildViewControllers):
        viewController = fb.evaluateExpression(
            "(id)[(id)[%s childViewControllers] objectAtIndex:%d]" % (vc, i)
        )
        s += _recursiveViewControllerDescriptionWithPrefixAndChildPrefix(
            viewController, string, nextPrefix, nextPrefix
        )

    if not isMac:
        isModal = fb.evaluateBooleanExpression(
            "%s != nil && ((id)[(id)[(id)%s presentedViewController] presentingViewController]) == %s"
            % (vc, vc, vc)
        )

        if isModal:
            modalVC = fb.evaluateObjectExpression(
                "(id)[(id)%s presentedViewController]" % (vc)
            )
            s += _recursiveViewControllerDescriptionWithPrefixAndChildPrefix(
                modalVC, string, childPrefix + "  *M", nextPrefix
            )
            s += "\n// '*M' means the view controller is presented modally."

    return string + s
