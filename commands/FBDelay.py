#!/usr/bin/python

# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from threading import Timer

import fbchisellldbbase as fb
import lldb


def lldbcommands():
    return [FBDelay()]


class FBDelay(fb.FBCommand):
    def name(self):
        return "zzz"

    def description(self):
        return "Executes specified lldb command after delay."

    def args(self):
        return [
            fb.FBCommandArgument(
                arg="delay in seconds",
                type="float",
                help="time to wait before executing specified command",
            ),
            fb.FBCommandArgument(
                arg="lldb command",
                type="string",
                help="another lldb command to execute after specified delay",
                default="process interrupt",
            ),
        ]

    def run(self, arguments, options):
        lldb.debugger.SetAsync(True)
        lldb.debugger.HandleCommand("process continue")
        delay = float(arguments[0])
        command = str(arguments[1])
        t = Timer(delay, lambda: self.runDelayed(command))
        t.start()

    def runDelayed(self, command):
        lldb.debugger.HandleCommand("process interrupt")
        lldb.debugger.HandleCommand(command)
