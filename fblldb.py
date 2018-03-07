#!/usr/bin/python

# Copyright (c) 2014, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

import lldb

import imp
import os

from optparse import OptionParser

import fblldbbase as fb

def __lldb_init_module(debugger, dict):
  filePath = os.path.realpath(__file__)
  lldbHelperDir = os.path.dirname(filePath)

  commandsDirectory = os.path.join(lldbHelperDir, 'commands')
  loadCommandsInDirectory(commandsDirectory)

def loadCommandsInDirectory(commandsDirectory):
  for file in os.listdir(commandsDirectory):
    fileName, fileExtension = os.path.splitext(file)
    if fileExtension == '.py':
      module = imp.load_source(fileName, os.path.join(commandsDirectory, file))

      if hasattr(module, 'lldbinit'):
        module.lldbinit()

      if hasattr(module, 'lldbcommands'):
        module._loadedFunctions = {}
        for command in module.lldbcommands():
          loadCommand(module, command, commandsDirectory, fileName, fileExtension)

def loadCommand(module, command, directory, filename, extension):
  func = makeRunCommand(command, os.path.join(directory, filename + extension))
  name = command.name()
  helpText = command.description().strip().splitlines()[0] # first line of description

  key = filename + '_' + name

  module._loadedFunctions[key] = func

  functionName = '__' + key

  lldb.debugger.HandleCommand('script ' + functionName + ' = sys.modules[\'' + module.__name__ + '\']._loadedFunctions[\'' + key + '\']')
  lldb.debugger.HandleCommand('command script add --help "{help}" --function {function} {name}'.format(
    help=helpText.replace('"', '\\"'), # escape quotes
    function=functionName,
    name=name))

def makeRunCommand(command, filename):
  def runCommand(debugger, input, exe_ctx, result, _):
    command.result = result
    command.context = exe_ctx
    splitInput = command.lex(input)

    # OptionParser will throw in the case where you want just one big long argument and no
    # options and you enter something that starts with '-' in the argument. e.g.:
    #     somecommand -[SomeClass someSelector:]
    # This solves that problem by prepending a '--' so that OptionParser does the right
    # thing.
    options = command.options()
    if len(options) == 0:
      if '--' not in splitInput:
        splitInput.insert(0, '--')

    parser = optionParserForCommand(command)
    (options, args) = parser.parse_args(splitInput)

    # When there are more args than the command has declared, assume
    # the initial args form an expression and combine them into a single arg.
    if len(args) > len(command.args()):
      overhead = len(args) - len(command.args())
      head = args[:overhead + 1] # Take N+1 and reduce to 1.
      args = [' '.join(head)] + args[-overhead:]

    if validateArgsForCommand(args, command):
      command.run(args, options)

  runCommand.__doc__ = helpForCommand(command, filename)
  return runCommand

def validateArgsForCommand(args, command):
  if len(args) < len(command.args()):
    defaultArgs = [arg.default for arg in command.args()]
    defaultArgsToAppend = defaultArgs[len(args):]

    index = len(args)
    for defaultArg in defaultArgsToAppend:
      if not defaultArg:
        arg = command.args()[index]
        print 'Whoops! You are missing the <' + arg.argName + '> argument.'
        print '\nUsage: ' + usageForCommand(command)
        return
      index += 1

    args.extend(defaultArgsToAppend)
  return True

def optionParserForCommand(command):
  parser = OptionParser()

  for argument in command.options():
    if argument.boolean:
      parser.add_option(argument.shortName, argument.longName, dest=argument.argName,
                        help=argument.help, action=("store_false" if argument.default else "store_true"))
    else:
      parser.add_option(argument.shortName, argument.longName, dest=argument.argName,
                        help=argument.help, default=argument.default)

  return parser

def helpForCommand(command, filename):
  help = command.description()

  argSyntax = ''
  optionSyntax = ''

  if command.args():
    help += '\n\nArguments:'
    for arg in command.args():
      help += '\n  <' + arg.argName + '>; '
      if arg.argType:
        help += 'Type: ' + arg.argType + '; '
      help += arg.help
      argSyntax += ' <' + arg.argName + '>'

  if command.options():
    help += '\n\nOptions:'
    for option in command.options():

      if option.longName and option.shortName:
        optionFlag = option.longName + '/' + option.shortName
      elif option.longName:
        optionFlag = option.longName
      else:
        optionFlag = option.shortName

      help += '\n  ' + optionFlag + ' '

      if not option.boolean:
        help += '<' + option.argName + '>; Type: ' + option.argType

      help += '; ' + option.help

      optionSyntax += ' [{name}{arg}]'.format(
        name=(option.longName or option.shortName),
        arg=('' if option.boolean else ('=' + option.argName))
      )

  help += '\n\nSyntax: ' + command.name() + optionSyntax + argSyntax

  help += '\n\nThis command is implemented as %s in %s.' % (command.__class__.__name__, filename)

  return help

def usageForCommand(command):
  usage = command.name()
  for arg in command.args():
    if arg.default:
      usage += ' [' + arg.argName + ']'
    else:
      usage += ' ' + arg.argName

  return usage
