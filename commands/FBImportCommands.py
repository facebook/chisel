#!/usr/bin/python

# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import fbchisellldbbase as fb
import lldb


def lldbcommands():
    return [ImportUIKitModule()]


class ImportUIKitModule(fb.FBCommand):
    def name(self):
        return "uikit"

    def description(self):
        return "Imports the UIKit module to get access to the types while in lldb."

    def run(self, arguments, options):
        frame = (
            lldb.debugger.GetSelectedTarget()
            .GetProcess()
            .GetSelectedThread()
            .GetSelectedFrame()
        )
        fb.importModule(frame, "UIKit")