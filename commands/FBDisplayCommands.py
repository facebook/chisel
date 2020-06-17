#!/usr/bin/python

# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import fbchisellldbbase as fb
import fbchisellldbobjcruntimehelpers as runtimeHelpers
import fbchisellldbviewcontrollerhelpers as viewControllerHelpers
import fbchisellldbviewhelpers as viewHelpers
import lldb


def lldbcommands():
    return [
        FBCoreAnimationFlushCommand(),
        FBDrawBorderCommand(),
        FBRemoveBorderCommand(),
        FBMaskViewCommand(),
        FBUnmaskViewCommand(),
        FBShowViewCommand(),
        FBHideViewCommand(),
        FBPresentViewControllerCommand(),
        FBDismissViewControllerCommand(),
        FBSlowAnimationCommand(),
        FBUnslowAnimationCommand(),
    ]


class FBDrawBorderCommand(fb.FBCommand):
    colors = [
        "black",
        "gray",
        "red",
        "green",
        "blue",
        "cyan",
        "yellow",
        "magenta",
        "orange",
        "purple",
        "brown",
    ]

    def name(self):
        return "border"

    def description(self):
        return "Draws a border around <viewOrLayer>. Color and width can be optionally provided. Additionally depth can be provided in order to recursively border subviews."

    def args(self):
        return [
            fb.FBCommandArgument(
                arg="viewOrLayer",
                type="UIView/NSView/CALayer *",
                help="The view/layer to border. NSViews must be layer-backed.",
            )
        ]

    def options(self):
        return [
            fb.FBCommandArgument(
                short="-c",
                long="--color",
                arg="color",
                type="string",
                default="red",
                help="A color name such as 'red', 'green', 'magenta', etc.",
            ),
            fb.FBCommandArgument(
                short="-w",
                long="--width",
                arg="width",
                type="CGFloat",
                default=2.0,
                help="Desired width of border.",
            ),
            fb.FBCommandArgument(
                short="-d",
                long="--depth",
                arg="depth",
                type="int",
                default=0,
                help="Number of levels of subviews to border. Each level gets a different color beginning with the provided or default color",
            ),
        ]

    def run(self, args, options):
        def setBorder(layer, width, color, colorClass):
            fb.evaluateEffect("[%s setBorderWidth:(CGFloat)%s]" % (layer, width))
            fb.evaluateEffect(
                "[%s setBorderColor:(CGColorRef)[(id)[%s %sColor] CGColor]]"
                % (layer, colorClass, color)
            )

        obj = fb.evaluateInputExpression(args[0])
        depth = int(options.depth)
        isMac = runtimeHelpers.isMacintoshArch()
        color = options.color
        assert color in self.colors, "Color must be one of the following: {}".format(
            " ".join(self.colors)
        )
        colorClassName = "UIColor"
        if isMac:
            colorClassName = "NSColor"

        if viewHelpers.isView(obj):
            prevLevel = 0
            for view, level in viewHelpers.subviewsOfView(obj):
                if level > depth:
                    break
                if prevLevel != level:
                    color = self.nextColorAfterColor(color)
                    prevLevel = level
                layer = viewHelpers.convertToLayer(view)
                setBorder(layer, options.width, color, colorClassName)
        else:
            # `obj` is not a view, make sure recursive bordering is not requested
            assert (
                depth <= 0
            ), "Recursive bordering is only supported for UIViews or NSViews"
            layer = viewHelpers.convertToLayer(obj)
            setBorder(layer, options.width, color, colorClassName)

        lldb.debugger.HandleCommand("caflush")

    def nextColorAfterColor(self, color):
        assert color in self.colors, "{} is not a supported color".format(color)
        return self.colors[(self.colors.index(color) + 1) % len(self.colors)]


class FBRemoveBorderCommand(fb.FBCommand):
    def name(self):
        return "unborder"

    def description(self):
        return "Removes border around <viewOrLayer>."

    def options(self):
        return [
            fb.FBCommandArgument(
                short="-d",
                long="--depth",
                arg="depth",
                type="int",
                default=0,
                help="Number of levels of subviews to unborder.",
            )
        ]

    def args(self):
        return [
            fb.FBCommandArgument(
                arg="viewOrLayer",
                type="UIView/NSView/CALayer *",
                help="The view/layer to unborder.",
            )
        ]

    def run(self, args, options):
        def setUnborder(layer):
            fb.evaluateEffect("[%s setBorderWidth:(CGFloat)%s]" % (layer, 0))

        obj = args[0]
        depth = int(options.depth)
        if viewHelpers.isView(obj):
            for view, level in viewHelpers.subviewsOfView(obj):
                if level > depth:
                    break
                layer = viewHelpers.convertToLayer(view)
                setUnborder(layer)
        else:
            # `obj` is not a view, make sure recursive unbordering is not requested
            assert (
                depth <= 0
            ), "Recursive unbordering is only supported for UIViews or NSViews"
            layer = viewHelpers.convertToLayer(obj)
            setUnborder(layer)

        lldb.debugger.HandleCommand("caflush")


class FBMaskViewCommand(fb.FBCommand):
    def name(self):
        return "mask"

    def description(self):
        return "Add a transparent rectangle to the window to reveal a possibly obscured or hidden view or layer's bounds"

    def args(self):
        return [
            fb.FBCommandArgument(
                arg="viewOrLayer",
                type="UIView/NSView/CALayer *",
                help="The view/layer to mask.",
            )
        ]

    def options(self):
        return [
            fb.FBCommandArgument(
                short="-c",
                long="--color",
                arg="color",
                type="string",
                default="red",
                help="A color name such as 'red', 'green', 'magenta', etc.",
            ),
            fb.FBCommandArgument(
                short="-a",
                long="--alpha",
                arg="alpha",
                type="CGFloat",
                default=0.5,
                help="Desired alpha of mask.",
            ),
        ]

    def run(self, args, options):
        viewOrLayer = fb.evaluateObjectExpression(args[0])
        viewHelpers.maskView(viewOrLayer, options.color, options.alpha)


class FBUnmaskViewCommand(fb.FBCommand):
    def name(self):
        return "unmask"

    def description(self):
        return "Remove mask from a view or layer"

    def args(self):
        return [
            fb.FBCommandArgument(
                arg="viewOrLayer",
                type="UIView/CALayer *",
                help="The view/layer to mask.",
            )
        ]

    def run(self, args, options):
        viewOrLayer = fb.evaluateObjectExpression(args[0])
        viewHelpers.unmaskView(viewOrLayer)


class FBCoreAnimationFlushCommand(fb.FBCommand):
    def name(self):
        return "caflush"

    def description(self):
        return "Force Core Animation to flush. This will 'repaint' the UI but also may mess with ongoing animations."

    def run(self, arguments, options):
        viewHelpers.flushCoreAnimationTransaction()


class FBShowViewCommand(fb.FBCommand):
    def name(self):
        return "show"

    def description(self):
        return "Show a view or layer."

    def args(self):
        return [
            fb.FBCommandArgument(
                arg="viewOrLayer",
                type="UIView/NSView/CALayer *",
                help="The view/layer to show.",
            )
        ]

    def run(self, args, options):
        viewHelpers.setViewHidden(args[0], False)


class FBHideViewCommand(fb.FBCommand):
    def name(self):
        return "hide"

    def description(self):
        return "Hide a view or layer."

    def args(self):
        return [
            fb.FBCommandArgument(
                arg="viewOrLayer",
                type="UIView/NSView/CALayer *",
                help="The view/layer to hide.",
            )
        ]

    def run(self, args, options):
        viewHelpers.setViewHidden(args[0], True)


class FBPresentViewControllerCommand(fb.FBCommand):
    def name(self):
        return "present"

    def description(self):
        return "Present a view controller."

    def args(self):
        return [
            fb.FBCommandArgument(
                arg="viewController",
                type="UIViewController *",
                help="The view controller to present.",
            )
        ]

    def run(self, args, option):
        viewControllerHelpers.presentViewController(args[0])


class FBDismissViewControllerCommand(fb.FBCommand):
    def name(self):
        return "dismiss"

    def description(self):
        return "Dismiss a presented view controller."

    def args(self):
        return [
            fb.FBCommandArgument(
                arg="viewController",
                type="UIViewController *",
                help="The view controller to dismiss.",
            )
        ]

    def run(self, args, option):
        viewControllerHelpers.dismissViewController(args[0])


class FBSlowAnimationCommand(fb.FBCommand):
    def name(self):
        return "slowanim"

    def description(self):
        return "Slows down animations. Works on the iOS Simulator and a device."

    def args(self):
        return [
            fb.FBCommandArgument(
                arg="speed",
                type="float",
                default=0.1,
                help="Animation speed (default 0.1).",
            )
        ]

    def run(self, args, option):
        viewHelpers.slowAnimation(args[0])


class FBUnslowAnimationCommand(fb.FBCommand):
    def name(self):
        return "unslowanim"

    def description(self):
        return "Turn off slow animations."

    def run(self, args, option):
        viewHelpers.slowAnimation()
