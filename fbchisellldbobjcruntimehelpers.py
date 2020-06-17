#!/usr/bin/python

# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import re

import fbchisellldbbase as fb
import lldb


def objc_getClass(className):
    command = '(void*)objc_getClass("{}")'.format(className)
    value = fb.evaluateExpression(command)
    return value


def object_getClass(object):
    command = "(void*)object_getClass((id){})".format(object)
    value = fb.evaluateExpression(command)
    return value


def class_getName(klass):
    command = "(const char*)class_getName((Class){})".format(klass)
    value = fb.evaluateExpressionValue(command).GetSummary().strip('"')
    return value


def class_getSuperclass(klass):
    command = "(void*)class_getSuperclass((Class){})".format(klass)
    value = fb.evaluateExpression(command)
    return value


def class_isMetaClass(klass):
    command = "class_isMetaClass((Class){})".format(klass)
    return fb.evaluateBooleanExpression(command)


def class_getInstanceMethod(klass, selector):
    command = "(void*)class_getInstanceMethod((Class){}, @selector({}))".format(
        klass, selector
    )
    value = fb.evaluateExpression(command)
    return value


def currentArch():
    targetTriple = lldb.debugger.GetSelectedTarget().GetTriple()
    arch = targetTriple.split("-")[0]
    if arch == "x86_64h":
        arch = "x86_64"
    return arch


def functionPreambleExpressionForSelf():
    import re

    arch = currentArch()
    expressionForSelf = None
    if arch == "i386":
        expressionForSelf = "*(id*)($esp+4)"
    elif arch == "x86_64":
        expressionForSelf = "(id)$rdi"
    elif arch == "arm64":
        expressionForSelf = "(id)$x0"
    elif re.match(r"^armv.*$", arch):
        expressionForSelf = "(id)$r0"
    return expressionForSelf


def functionPreambleExpressionForObjectParameterAtIndex(parameterIndex):
    arch = currentArch()
    expresssion = None
    if arch == "i386":
        expresssion = "*(id*)($esp + " + str(12 + parameterIndex * 4) + ")"
    elif arch == "x86_64":
        if parameterIndex > 3:
            raise Exception(
                "Current implementation can not return object at index greater than 3 for x86_64"
            )
        registersList = ["rdx", "rcx", "r8", "r9"]
        expresssion = "(id)$" + registersList[parameterIndex]
    elif arch == "arm64":
        if parameterIndex > 5:
            raise Exception(
                "Current implementation can not return object at index greater than 5 for arm64"
            )
        expresssion = "(id)$x" + str(parameterIndex + 2)
    elif re.match(r"^armv.*$", arch):
        if parameterIndex > 1:
            raise Exception(
                "Current implementation can not return object at index greater than 1 for arm32"
            )
        expresssion = "(id)$r" + str(parameterIndex + 2)
    return expresssion


def isMacintoshArch():
    arch = currentArch()
    if not arch == "x86_64":
        return False

    nsClassName = "NSApplication"
    command = '(void*)objc_getClass("{}")'.format(nsClassName)

    return fb.evaluateBooleanExpression(command + "!= nil")


def isIOSSimulator():
    return (
        fb.evaluateExpressionValue("(id)[[UIDevice currentDevice] model]")
        .GetObjectDescription()
        .lower()
        .find("simulator")
        >= 0
    )


def isIOSDevice():
    return not isMacintoshArch() and not isIOSSimulator()
