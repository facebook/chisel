#!/usr/bin/python

# Copyright (c) 2014, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

import os
import re
import subprocess

import lldb
import fblldbbase as fb
import fblldbviewcontrollerhelpers as vcHelpers
import fblldbviewhelpers as viewHelpers
import fblldbobjcruntimehelpers as runtimeHelpers

def lldbcommands():
  return [
    FBPrintViewHierarchyCommand(),
    FBPrintCoreAnimationTree(),
    FBPrintViewControllerHierarchyCommand(),
    FBPrintIsExecutingInAnimationBlockCommand(),
    FBPrintInheritanceHierarchy(),
    FBPrintUpwardResponderChain(),
    FBPrintOnscreenTableView(),
    FBPrintOnscreenTableViewCells(),
    FBPrintInternals(),
    FBPrintInstanceVariable(),
    FBPrintKeyPath(),
    FBPrintApplicationDocumentsPath(),
    FBPrintApplicationBundlePath(),
    FBPrintData(),
    FBPrintTargetActions(),
    FBPrintJSON(),
    FBPrintSwiftJSON(),
    FBPrintAsCurl(),
    FBPrintToClipboard(),
    FBPrintObjectInObjc(),
  ]

class FBPrintViewHierarchyCommand(fb.FBCommand):
  def name(self):
    return 'pviews'

  def description(self):
    return 'Print the recursion description of <aView>.'

  def options(self):
    return [
      fb.FBCommandArgument(short='-u', long='--up', arg='upwards', boolean=True, default=False, help='Print only the hierarchy directly above the view, up to its window.'),
      fb.FBCommandArgument(short='-d', long='--depth', arg='depth', type='int', default="0", help='Print only to a given depth. 0 indicates infinite depth.'),
      fb.FBCommandArgument(short='-w', long='--window', arg='window', type='int', default="0", help='Specify the window to print a description of. Check which windows exist with "po (id)[[UIApplication sharedApplication] windows]".'),
    ]

  def args(self):
    return [ fb.FBCommandArgument(arg='aView', type='UIView*/NSView*', help='The view to print the description of.', default='__keyWindow_dynamic__') ]

  def run(self, arguments, options):
    maxDepth = int(options.depth)
    window = int(options.window)
    isMac = runtimeHelpers.isMacintoshArch()

    if window > 0:
      if isMac:
        arguments[0] = '(id)[[[[NSApplication sharedApplication] windows] objectAtIndex:' + str(window) + '] contentView]'
      else:
        arguments[0] = '(id)[[[UIApplication sharedApplication] windows] objectAtIndex:' + str(window) + ']'
    elif arguments[0] == '__keyWindow_dynamic__':
      if isMac:
        arguments[0] = '(id)[[[[NSApplication sharedApplication] windows] objectAtIndex:0] contentView]'
      else:
        arguments[0] = '(id)[[UIApplication sharedApplication] keyWindow]'

    if options.upwards:
      view = arguments[0]
      description = viewHelpers.upwardsRecursiveDescription(view, maxDepth)
      if description:
        print description
      else:
        print 'Failed to walk view hierarchy. Make sure you pass a view, not any other kind of object or expression.'
    else:
      printingMethod = 'recursiveDescription'
      if isMac:
        printingMethod = '_subtreeDescription'

      description = fb.evaluateExpressionValue('(id)[' + arguments[0] + ' ' + printingMethod + ']').GetObjectDescription()
      if maxDepth > 0:
        separator = re.escape("   | ")
        prefixToRemove = separator * maxDepth + " "
        description += "\n"
        description = re.sub(r'%s.*\n' % (prefixToRemove), r'', description)
      print description

class FBPrintCoreAnimationTree(fb.FBCommand):
  def name(self):
    return 'pca'

  def description(self):
    return 'Print layer tree from the perspective of the render server.'

  def run(self, arguments, options):
    print fb.describeObject('[NSString stringWithCString:(char *)CARenderServerGetInfo(0, 2, 0)]')


class FBPrintViewControllerHierarchyCommand(fb.FBCommand):
  def name(self):
    return 'pvc'

  def description(self):
    return 'Print the recursion description of <aViewController>.'

  def args(self):
    return [ fb.FBCommandArgument(arg='aViewController', type='UIViewController*', help='The view controller to print the description of.', default='__keyWindow_rootVC_dynamic__') ]

  def run(self, arguments, options):
    isMac = runtimeHelpers.isMacintoshArch()

    if arguments[0] == '__keyWindow_rootVC_dynamic__':
      if fb.evaluateBooleanExpression('[UIViewController respondsToSelector:@selector(_printHierarchy)]'):
        print fb.describeObject('[UIViewController _printHierarchy]')
        return

      arguments[0] = '(id)[(id)[[UIApplication sharedApplication] keyWindow] rootViewController]'
      if isMac:
        arguments[0] = '(id)[[[[NSApplication sharedApplication] windows] objectAtIndex:0] contentViewController]'

    print vcHelpers.viewControllerRecursiveDescription(arguments[0])


class FBPrintIsExecutingInAnimationBlockCommand(fb.FBCommand):
  def name(self):
    return 'panim'

  def description(self):
    return 'Prints if the code is currently execution with a UIView animation block.'

  def run(self, arguments, options):
    lldb.debugger.HandleCommand('p (BOOL)[UIView _isInAnimationBlock]')


def _printIterative(initialValue, generator):
  indent = 0
  for currentValue in generator(initialValue):
    print '   | ' * indent + currentValue
    indent += 1


class FBPrintInheritanceHierarchy(fb.FBCommand):
  def name(self):
    return 'pclass'

  def description(self):
    return 'Print the inheritance starting from an instance of any class.'

  def args(self):
    return [ fb.FBCommandArgument(arg='object', type='id', help='The instance to examine.') ]

  def run(self, arguments, options):
    _printIterative(arguments[0], _inheritanceHierarchy)

def _inheritanceHierarchy(instanceOfAClass):
  instanceAddress = fb.evaluateExpression(instanceOfAClass)
  instanceClass = fb.evaluateExpression('(id)[(id)' + instanceAddress + ' class]')
  while int(instanceClass, 16):
    yield fb.evaluateExpressionValue(instanceClass).GetObjectDescription()
    instanceClass = fb.evaluateExpression('(id)[(id)' + instanceClass + ' superclass]')


class FBPrintUpwardResponderChain(fb.FBCommand):
  def name(self):
    return 'presponder'

  def description(self):
    return 'Print the responder chain starting from a specific responder.'

  def args(self):
    return [ fb.FBCommandArgument(arg='startResponder', type='UIResponder *', help='The responder to use to start walking the chain.') ]

  def run(self, arguments, options):
    startResponder = fb.evaluateInputExpression(arguments[0])

    isMac = runtimeHelpers.isMacintoshArch()
    responderClass = 'UIResponder'
    if isMac:
      responderClass = 'NSResponder'

    if not fb.evaluateBooleanExpression('(BOOL)[(id)' + startResponder + ' isKindOfClass:[' + responderClass + ' class]]'):
      print 'Whoa, ' + startResponder + ' is not a ' + responderClass + '. =('
      return

    _printIterative(startResponder, _responderChain)

def _responderChain(startResponder):
  responderAddress = fb.evaluateExpression(startResponder)
  while int(responderAddress, 16):
    yield fb.evaluateExpressionValue(responderAddress).GetObjectDescription()
    responderAddress = fb.evaluateExpression('(id)[(id)' + responderAddress + ' nextResponder]')


def tableViewInHierarchy():
  viewDescription = fb.evaluateExpressionValue('(id)[(id)[[UIApplication sharedApplication] keyWindow] recursiveDescription]').GetObjectDescription()

  searchView = None

  # Try to find an instance of
  classPattern = re.compile(r'UITableView: (0x[0-9a-fA-F]+);')
  for match in re.finditer(classPattern, viewDescription):
    searchView = match.group(1)
    break

  # Try to find a direct subclass
  if not searchView:
    subclassPattern = re.compile(r'(0x[0-9a-fA-F]+); baseClass = UITableView;')
    for match in re.finditer(subclassPattern, viewDescription):
      searchView = match.group(1)
      break

  # SLOW: check every pointer in town
  if not searchView:
    pattern = re.compile(r'(0x[0-9a-fA-F]+)[;>]')
    for (view) in re.findall(pattern, viewDescription):
      if fb.evaluateBooleanExpression('[' + view + ' isKindOfClass:(id)[UITableView class]]'):
        searchView = view
        break

  return searchView

class FBPrintOnscreenTableView(fb.FBCommand):
  def name(self):
    return 'ptv'

  def description(self):
    return 'Print the highest table view in the hierarchy.'

  def run(self, arguments, options):
    tableView = tableViewInHierarchy()
    if tableView:
      viewValue = fb.evaluateExpressionValue(tableView)
      print viewValue.GetObjectDescription()
      cmd = 'echo %s | tr -d "\n" | pbcopy' % tableView
      os.system(cmd)
    else:
      print 'Sorry, chump. I couldn\'t find a table-view. :\'('

class FBPrintOnscreenTableViewCells(fb.FBCommand):
  def name(self):
    return 'pcells'

  def description(self):
    return 'Print the visible cells of the highest table view in the hierarchy.'

  def run(self, arguments, options):
    tableView = tableViewInHierarchy()
    print fb.evaluateExpressionValue('(id)[(id)' + tableView + ' visibleCells]').GetObjectDescription()


class FBPrintInternals(fb.FBCommand):
  def name(self):
    return 'pinternals'

  def description(self):
    return 'Show the internals of an object by dereferencing it as a pointer.'

  def args(self):
    return [ fb.FBCommandArgument(arg='object', type='id', help='Object expression to be evaluated.') ]
  
  def options(self):
    return [
          fb.FBCommandArgument(arg='appleWay', short='-a', long='--apple', boolean=True, default=False, help='Print ivars the apple way')
    ]

  def run(self, arguments, options):
    object = fb.evaluateObjectExpression(arguments[0])
    if options.appleWay:
        if fb.evaluateBooleanExpression('[{} respondsToSelector:@selector(_ivarDescription)]'.format(object)):
            command = 'po [{} _ivarDescription]'.format(object)
        else:
            print 'Sorry, but it seems Apple dumped the _ivarDescription method'
            return
    else:
        objectClass = fb.evaluateExpressionValue('(id)[(id)(' + object + ') class]').GetObjectDescription()
        command = 'p *(({} *)((id){}))'.format(objectClass, object)
    lldb.debugger.HandleCommand(command)


class FBPrintInstanceVariable(fb.FBCommand):
  def name(self):
    return 'pivar'

  def description(self):
    return "Print the value of an object's named instance variable."

  def args(self):
    return [
      fb.FBCommandArgument(arg='object', type='id', help='Object expression to be evaluated.'),
      fb.FBCommandArgument(arg='ivarName', help='Name of instance variable to print.')
    ]

  def run(self, arguments, options):
    object = fb.evaluateInputExpression(arguments[0])
    ivarName = arguments[1]

    objectClass = fb.evaluateExpressionValue('(id)[(' + object + ') class]').GetObjectDescription()

    ivarTypeCommand = '((char *)ivar_getTypeEncoding((void*)object_getInstanceVariable((id){}, \"{}\", 0)))[0]'.format(object, ivarName)
    ivarTypeEncodingFirstChar = fb.evaluateExpression(ivarTypeCommand)

    result = fb.evaluateExpressionValue('(({} *)({}))->{}'.format(objectClass, object, ivarName))
    print result.GetObjectDescription() if '@' in ivarTypeEncodingFirstChar else result

class FBPrintKeyPath(fb.FBCommand):
  def name(self):
    return 'pkp'

  def description(self):
    return "Print out the value of the key path expression using -valueForKeyPath:"

  def args(self):
    return [
      fb.FBCommandArgument(arg='keypath', type='NSString *', help='The keypath to print'),
    ]

  def run(self, arguments, options):
    command = arguments[0]
    if len(command.split('.')) == 1:
      lldb.debugger.HandleCommand("po " + command)
    else:
      objectToMessage, keypath = command.split('.', 1)
      object = fb.evaluateObjectExpression(objectToMessage)
      print fb.describeObject('[{} valueForKeyPath:@"{}"]'.format(object, keypath))


class FBPrintApplicationDocumentsPath(fb.FBCommand):
  def name(self):
    return 'pdocspath'

  def description(self):
    return "Print application's 'Documents' directory path."

  def options(self):
    return [
      fb.FBCommandArgument(short='-o', long='--open', arg='open', boolean=True, default=False, help='open in Finder'),
    ]

  def run(self, arguments, options):
    # in iOS SDK NSDocumentDirectory == 9  NSUserDomainMask == 1
    NSDocumentDirectory = '9'
    NSUserDomainMask = '1'
    path = fb.evaluateExpressionValue('(NSString*)[NSSearchPathForDirectoriesInDomains(' + NSDocumentDirectory + ', ' + NSUserDomainMask + ', YES) lastObject]')
    pathString = '{}'.format(path).split('"')[1]
    cmd = 'echo {} | tr -d "\n" | pbcopy'.format(pathString)
    os.system(cmd)
    print pathString
    if options.open:
      os.system('open '+ pathString)


class FBPrintApplicationBundlePath(fb.FBCommand):
  def name(self):
    return 'pbundlepath'

  def description(self):
    return "Print application's bundle directory path."

  def options(self):
    return [
      fb.FBCommandArgument(short='-o', long='--open', arg='open', boolean=True, default=False, help='open in Finder'),
    ]

  def run(self, arguments, options):
    path = fb.evaluateExpressionValue('(NSString*)[[NSBundle mainBundle] bundlePath]')
    pathString = '{}'.format(path).split('"')[1]
    cmd = 'echo {} | tr -d "\n" | pbcopy'.format(pathString)
    os.system(cmd)
    print pathString
    if options.open:
      os.system('open '+ pathString)


class FBPrintData(fb.FBCommand):
  def name(self):
    return 'pdata'

  def description(self):
    return 'Print the contents of NSData object as string.\n' \
           'Supported encodings:\n' \
           '- ascii,\n' \
           '- utf8,\n' \
           '- utf16, unicode,\n' \
           '- utf16l (Little endian),\n' \
           '- utf16b (Big endian),\n' \
           '- utf32,\n' \
           '- utf32l (Little endian),\n' \
           '- utf32b (Big endian),\n' \
           '- latin1, iso88591 (88591),\n' \
           '- latin2, iso88592 (88592),\n' \
           '- cp1251 (1251),\n' \
           '- cp1252 (1252),\n' \
           '- cp1253 (1253),\n' \
           '- cp1254 (1254),\n' \
           '- cp1250 (1250),' \

  def options(self):
    return [
      fb.FBCommandArgument(arg='encoding', short='-e', long='--encoding', type='string', help='Used encoding (default utf-8).', default='utf-8')
    ]

  def args(self):
    return [
      fb.FBCommandArgument(arg='data', type='NSData *', help='NSData object.')
    ]

  def run(self, arguments, option):
    # Normalize encoding.
    encoding_text = option.encoding.lower().replace(' -', '')
    enc = 4  # Default encoding UTF-8.
    if encoding_text == 'ascii':
      enc = 1
    elif encoding_text == 'utf8':
      enc = 4
    elif encoding_text == 'latin1' or encoding_text == '88591' or encoding_text == 'iso88591':
      enc = 5
    elif encoding_text == 'latin2' or encoding_text == '88592' or encoding_text == 'iso88592':
      enc = 9
    elif encoding_text == 'unicode' or encoding_text == 'utf16':
      enc = 10
    elif encoding_text == '1251' or encoding_text == 'cp1251':
      enc = 11
    elif encoding_text == '1252' or encoding_text == 'cp1252':
      enc = 12
    elif encoding_text == '1253' or encoding_text == 'cp1253':
      enc = 13
    elif encoding_text == '1254' or encoding_text == 'cp1254':
      enc = 14
    elif encoding_text == '1250' or encoding_text == 'cp1250':
      enc = 15
    elif encoding_text == 'utf16b':
      enc = 0x90000100
    elif encoding_text == 'utf16l':
      enc = 0x94000100
    elif encoding_text == 'utf32':
      enc = 0x8c000100
    elif encoding_text == 'utf32b':
      enc = 0x98000100
    elif encoding_text == 'utf32l':
      enc = 0x9c000100

    print fb.describeObject('[[NSString alloc] initWithData:{} encoding:{}]'.format(arguments[0], enc))

class FBPrintTargetActions(fb.FBCommand):

  def name(self):
    return 'pactions'

  def description(self):
    return 'Print the actions and targets of a control.'

  def args(self):
    return [ fb.FBCommandArgument(arg='control', type='UIControl *', help='The control to inspect the actions of.') ]

  def run(self, arguments, options):
    control = fb.evaluateInputExpression(arguments[0])
    targets = fb.evaluateObjectExpression('[[{control} allTargets] allObjects]'.format(control=control))
    targetCount = fb.evaluateIntegerExpression('[{targets} count]'.format(targets=targets))

    for index in range(0, targetCount):
      target = fb.evaluateObjectExpression('[{targets} objectAtIndex:{index}]'.format(targets=targets, index=index))
      actions = fb.evaluateObjectExpression('[{control} actionsForTarget:{target} forControlEvent:0]'.format(control=control, target=target))

      targetDescription = fb.evaluateExpressionValue('(id){target}'.format(target=target)).GetObjectDescription()
      actionsDescription = fb.evaluateExpressionValue('(id)[{actions} componentsJoinedByString:@", "]'.format(actions=actions)).GetObjectDescription()

      print '{target}: {actions}'.format(target=targetDescription, actions=actionsDescription)

class FBPrintJSON(fb.FBCommand):

  def name(self):
    return 'pjson'

  def description(self):
    return 'Print JSON representation of NSDictionary or NSArray object'

  def options(self):
    return [
      fb.FBCommandArgument(arg='plain', short='-p', long='--plain', boolean=True, default=False, help='Plain JSON')
    ]

  def args(self):
    return [ fb.FBCommandArgument(arg='object', type='id', help='The NSDictionary or NSArray object to print') ]

  def run(self, arguments, options):
    objectToPrint = fb.evaluateInputExpression(arguments[0])
    pretty = 1 if options.plain is None else 0
    jsonData = fb.evaluateObjectExpression('[NSJSONSerialization dataWithJSONObject:(id){} options:{} error:nil]'.format(objectToPrint, pretty))
    jsonString = fb.evaluateExpressionValue('(NSString*)[[NSString alloc] initWithData:(id){} encoding:4]'.format(jsonData)).GetObjectDescription()

    print jsonString

class FBPrintSwiftJSON(fb.FBCommand):
    
  def name(self):
      return 'psjson'
      
  def description(self):
      return 'Print JSON representation of Swift Dictionary or Swift Array object'
          
  def options(self):
      return [ fb.FBCommandArgument(arg='plain', short='-p', long='--plain', boolean=True, default=False, help='Plain JSON') ]
          
  def args(self):
      return [ fb.FBCommandArgument(arg='object', type='NSObject *', help='The Swift Dictionary or Swift Array to print') ]
          
  def run(self, arguments, options):
      #Convert to NSObject first to allow for objc runtime to process it
      objectToPrint = fb.evaluateInputExpression('{obj} as NSObject'.format(obj=arguments[0]))
      pretty = 1 if options.plain is None else 0
      jsonData = fb.evaluateObjectExpression('[NSJSONSerialization dataWithJSONObject:(NSObject*){} options:{} error:nil]'.format(objectToPrint, pretty))
      jsonString = fb.evaluateExpressionValue('(NSString*)[[NSString alloc] initWithData:(NSObject*){} encoding:4]'.format(jsonData)).GetObjectDescription()

      print jsonString

class FBPrintAsCurl(fb.FBCommand):
  def name(self):
    return 'pcurl'

  def description(self):
    return 'Print the NSURLRequest (HTTP) as curl command.'

  def options(self):
    return [
      fb.FBCommandArgument(short='-e', long='--embed-data', arg='embed', boolean=True, default=False, help='Embed request data as base64.'),
    ]

  def args(self):
    return [ fb.FBCommandArgument(arg='request', type='NSURLRequest*/NSMutableURLRequest*', help='The request to convert to the curl command.') ]

  def generateTmpFilePath(self):
    return '/tmp/curl_data_{}'.format(fb.evaluateExpression('(NSTimeInterval)[NSDate timeIntervalSinceReferenceDate]'))

  def run(self, arguments, options):
    request = fb.evaluateInputExpression(arguments[0])
    HTTPHeaderSring = ''
    HTTPMethod = fb.evaluateExpressionValue('(id)[{} HTTPMethod]'.format(request)).GetObjectDescription()
    URL = fb.evaluateExpressionValue('(id)[{} URL]'.format(request)).GetObjectDescription()
    timeout = fb.evaluateExpression('(NSTimeInterval)[{} timeoutInterval]'.format(request))
    HTTPHeaders = fb.evaluateObjectExpression('(id)[{} allHTTPHeaderFields]'.format(request))
    HTTPHeadersCount = fb.evaluateIntegerExpression('[{} count]'.format(HTTPHeaders))
    allHTTPKeys = fb.evaluateObjectExpression('[{} allKeys]'.format(HTTPHeaders))
    for index in range(0, HTTPHeadersCount):
        key = fb.evaluateObjectExpression('[{} objectAtIndex:{}]'.format(allHTTPKeys, index))
        keyDescription = fb.evaluateExpressionValue('(id){}'.format(key)).GetObjectDescription()
        value = fb.evaluateExpressionValue('(id)[(id){} objectForKey:{}]'.format(HTTPHeaders, key)).GetObjectDescription()
        if len(HTTPHeaderSring) > 0:
            HTTPHeaderSring += ' '
        HTTPHeaderSring += '-H "{}: {}"'.format(keyDescription, value)
    HTTPData = fb.evaluateObjectExpression('[{} HTTPBody]'.format(request))
    dataFile = None
    dataAsString = None
    if fb.evaluateIntegerExpression('[{} length]'.format(HTTPData)) > 0:
        if options.embed:
          if fb.evaluateIntegerExpression('[{} respondsToSelector:@selector(base64EncodedStringWithOptions:)]'.format(HTTPData)):
            dataAsString = fb.evaluateExpressionValue('(id)[(id){} base64EncodedStringWithOptions:0]'.format(HTTPData)).GetObjectDescription()
          else :
            print 'This version of OS doesn\'t supports base64 data encoding'
            return False
        elif not runtimeHelpers.isIOSDevice():
          dataFile = self.generateTmpFilePath()
          if not fb.evaluateBooleanExpression('(BOOL)[{} writeToFile:@"{}" atomically:NO]'.format(HTTPData, dataFile)):
            print 'Can\'t write data to file {}'.format(dataFile)
            return False
        else:
          print 'HTTPBody data for iOS Device is supported only with "--embed-data" flag'
          return False

    commandString = ''
    if dataAsString is not None and len(dataAsString) > 0:
      dataFile = self.generateTmpFilePath()
      commandString += 'echo "{}" | base64 -D -o "{}" && '.format(dataAsString, dataFile)
    commandString += 'curl -X {} --connect-timeout {}'.format(HTTPMethod, timeout)
    if len(HTTPHeaderSring) > 0:
        commandString += ' ' + HTTPHeaderSring
    if dataFile is not None:
        commandString += ' --data-binary @"{}"'.format(dataFile)

    commandString += ' "{}"'.format(URL)
    print commandString

class FBPrintToClipboard(fb.FBCommand):
  def name(self):
    return 'pbcopy'

  def description(self):
    return 'Print object and copy output to clipboard'

  def args(self):
    return [ fb.FBCommandArgument(arg='object', type='id', help='The object to print') ]

  def run(self, arguments, options):
    lldbOutput = fb.evaluateExpressionValue("[{changeset} description]".format(changeset = arguments[0])).GetObjectDescription()
    process = subprocess.Popen(
        'pbcopy', env={'LANG': 'en_US.UTF-8'}, stdin=subprocess.PIPE)
    process.communicate(lldbOutput.encode('utf-8'))
    print "Object copied to clipboard"

class FBPrintObjectInObjc(fb.FBCommand):
  def name(self):
    return 'poobjc'

  def description(self):
    return 'Print the expression result, with the expression run in an ObjC++ context. (Shortcut for "expression -O -l ObjC++ -- " )'

  def args(self):
    return [
      fb.FBCommandArgument(arg='expression', help='ObjC expression to evaluate and print.'),
    ]

  def run(self, arguments, options):
    expression = arguments[0]
    lldb.debugger.HandleCommand('expression -O -l ObjC++ -- ' + expression)
