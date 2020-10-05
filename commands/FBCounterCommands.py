#!/usr/bin/python

# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

# These set of commands provide a way to use counters in debug time. By using these counters,
# you can track how many times your program takes a specific path.
#
# Sample Use Case:
# Let's say you have a function that logs some messages from various parts of your code.
# And you want to learn how many times logMessage is called on startup.
#
# 1. Add a breakpoint to the entry point of your program (e.g. main).
#   a. Add `zzz 10 printcounter` as an action.
#   b. Check "Automatically continue after evaluating actions"
# 2. Add a breakpoint to the logMessage function.
#   a. Add `incrementcounter log` as an action.
#   b. Add `incrementcounter log_{} message` as an action.
#   c. Check "Automatically continue after evaluating actions"
# 3. Run the program
#
# Format String:
# It uses Python's string.Formatter to format strings. You can use placeholders here as you can in Python:
# https://docs.python.org/3.4/library/string.html#string.Formatter.format
#
# Sample key_format_string:
# "key_{}" (int)5 -> Will build the key string as "key_5"

# Can be removed when Python 2 support is removed.
from __future__ import print_function


import fbchisellldbbase as fb


counters = {}


def lldbcommands():
    return [
        FBIncrementCounterCommand(),
        FBPrintCounterCommand(),
        FBPrintCountersCommand(),
        FBResetCounterCommand(),
        FBResetCountersCommand(),
    ]


def generateKey(arguments):
    keyFormatString = arguments[1]
    keyArgs = []

    for argument in arguments[2:]:
        if argument.startswith('('):
            value = fb.evaluateExpression(argument)
        else:
            value = fb.evaluateExpressionValue(argument).GetObjectDescription()

            if not value:
                value = fb.evaluateExpression(argument)

        keyArgs.append(value)

    return keyFormatString.format(*keyArgs).strip()


# Increments the counter for the key.
# (lldb) incrementcounter key_format_string key_args
class FBIncrementCounterCommand(fb.FBCommand):
    def name(self):
        return "incrementcounter"

    def description(self):
        return "Increments the counter for the key."

    def run(self, arguments, options):
        key = generateKey(arguments)
        counters[key] = counters.get(key, 0) + 1


# Prints the counter for the key.
# (lldb) printcounter key_format_string key_args
# 0
class FBPrintCounterCommand(fb.FBCommand):
    def name(self):
        return "printcounter"

    def description(self):
        return "Prints the counter for the key."

    def run(self, arguments, options):
        key = generateKey(arguments)
        print(str(counters[key]))



# Prints all the counters sorted by the keys.
# (lldb) printcounters
# key_1: 0
class FBPrintCountersCommand(fb.FBCommand):
    def name(self):
        return "printcounters"

    def description(self):
        return "Prints all the counters sorted by the keys."

    def run(self, arguments, options):
        keys = sorted(counters.keys())
        for key in keys:
            print(key + ': ' + str(counters[key]))


# Resets the counter for the key.
# (lldb) resetcounter key_format_string key_args
class FBResetCounterCommand(fb.FBCommand):
    def name(self):
        return "resetcounter"

    def description(self):
        return "Resets the counter for the key."

    def run(self, arguments, options):
        key = generateKey(arguments)
        counters[key] = 0


# Resets all the counters.
# (lldb) resetcounters
class FBResetCountersCommand(fb.FBCommand):
    def name(self):
        return "resetcounters"

    def description(self):
        return "Resets all the counters."

    def run(self, arguments, options):
        counters.clear()
