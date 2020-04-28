#!/usr/bin/python

# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import print_function
import os
import time

import lldb
import errno
import fbchisellldbbase as fb
import fbchisellldbobjecthelpers as objectHelpers


def lldbcommands():
    return [FBCopyCommand()]


def _copyFromURL(url, preferredFilename, noOpen):
    data = fb.evaluateObjectExpression(
        '(id)[NSData dataWithContentsOfURL:(id){}]'.format(url)
    )
    defaultFilename = fb.describeObject(
        '(id)[[{} pathComponents] lastObject]'.format(url)
    )
    _copyFromData(data, defaultFilename, preferredFilename, noOpen)


def _copyFromData(data, defaultFilename, preferredFilename, noOpen):
    directory = '/tmp/chisel_copy/'

    path = directory + (preferredFilename or defaultFilename)

    try:
        os.makedirs(directory)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(directory):
            pass
        else:
            raise

    startAddress = fb.evaluateExpression('(void *)[(id)' + data + ' bytes]')
    length = fb.evaluateExpression('(NSUInteger)[(id)' + data + ' length]')

    address = int(startAddress, 16)
    length = int(length)

    if not (address or length):
        print('Could not get data.')
        return

    process = lldb.debugger.GetSelectedTarget().GetProcess()
    error = lldb.SBError()
    mem = process.ReadMemory(address, length, error)

    if error is not None and str(error) != 'success':
        print(error)
    else:
        with open(path, 'wb') as file:
            file.write(mem)
            file.close()
        print(path)
        if not noOpen:
            os.system('open ' + path)


def _copy(target, preferredFilename, noOpen):
    target = '(' + target + ')'

    if objectHelpers.isKindOfClass(target, 'NSURL'):
        _copyFromURL(target, preferredFilename, noOpen)
    elif objectHelpers.isKindOfClass(target, 'NSData'):
        _copyFromData(
            target,
            time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime()) + ".data",
            preferredFilename,
            noOpen
        )
    else:
        print('{} isn\'t supported. You can copy an NSURL or NSData.'.format(
            objectHelpers.className(target)
        ))


class FBCopyCommand(fb.FBCommand):
    def name(self):
        return 'copy'

    def description(self):
        return 'Copy data to your Mac.'

    def options(self):
        return [
            fb.FBCommandArgument(
                short='-f', long='--filename', arg='filename',
                help='The output filename.'
            ),
            fb.FBCommandArgument(
                short='-n', long='--no-open', arg='noOpen',
                boolean=True, default=False,
                help='Do not open the file.'
            ),
        ]

    def args(self):
        return [
            fb.FBCommandArgument(
                arg='target', type='(id)', help='The object to copy.'
            )
        ]

    def run(self, arguments, options):
        _copy(arguments[0], options.filename, options.noOpen)
