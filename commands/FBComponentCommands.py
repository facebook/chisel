#!/usr/bin/python

# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import fbchisellldbbase as fb
import fbchisellldbviewhelpers as viewHelpers


def lldbcommands():
    return [
        FBComponentsDebugCommand(),
        FBComponentsPrintCommand(),
        FBComponentsReflowCommand(),
    ]


class FBComponentsDebugCommand(fb.FBCommand):
    def name(self):
        return "dcomponents"

    def description(self):
        return "Set debugging options for components."

    def options(self):
        return [
            fb.FBCommandArgument(
                short="-s",
                long="--set",
                arg="set",
                help="Set debug mode for components",
                boolean=True,
            ),
            fb.FBCommandArgument(
                short="-u",
                long="--unset",
                arg="unset",
                help="Unset debug mode for components",
                boolean=True,
            ),
        ]

    def run(self, arguments, options):
        print("Debug mode for ComponentKit is deprecated; use Flipper instead.")


class FBComponentsPrintCommand(fb.FBCommand):
    def name(self):
        return "pcomponents"

    def description(self):
        return (
            "Print a recursive description of components found starting from <aView>."
        )

    def args(self):
        return [
            fb.FBCommandArgument(
                arg="aView",
                type="UIView* or CKComponent*",
                help="The view or component from which the search for components begins.",
                default="(id)[[UIApplication sharedApplication] keyWindow]",
            )
        ]

    def run(self, arguments, options):
        view = fb.evaluateInputExpression(arguments[0])
        if not viewHelpers.isView(view):
            # assume it's a CKComponent
            view = fb.evaluateExpression("((CKComponent *)%s).viewContext.view" % view)
        print(
            fb.describeObject(
                "[CKComponentHierarchyDebugHelper componentHierarchyDescriptionForView:(UIView *)"
                + view
                + "]"
            )
        )


class FBComponentsReflowCommand(fb.FBCommand):
    def name(self):
        return "rcomponents"

    def description(self):
        return "Synchronously reflow and update all components."

    def run(self, arguments, options):
        fb.evaluateEffect("[CKComponentDebugController reflowComponents]")
