#!/usr/bin/python

# Copyright (c) 2017, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

import lldb
import fblldbbase as fb
import re

NOT_FOUND = 0xffffffff  # UINT32_MAX


def lldbcommands():
  return [
    FBXCPrintDebugDescription(),
    FBXCPrintTree(),
    FBXCPrintObject(),
    FBXCNoId(),
  ]


class FBXCPrintDebugDescription(fb.FBCommand):
  def name(self):
    return 'xdebug'

  def description(self):
    return 'Print debug description the XCUIElement in human readable format.'

  def args(self):
    return [fb.FBCommandArgument(arg='element', type='XCUIElement*', help='The element to print debug description.', default='__default__')]

  def run(self, arguments, options):
    element = arguments[0]
    language = fb.currentLanguage()

    if element == '__default__':
      element = 'XCUIApplication()' if language == lldb.eLanguageTypeSwift else '(XCUIApplication *)[[XCUIApplication alloc] init]'

    if language == lldb.eLanguageTypeSwift:
      print fb.evaluateExpressionValue("{}.debugDescription".format(element), language=language) \
        .GetObjectDescription() \
        .replace("\\n", "\n") \
        .replace("\\'", "'") \
        .strip(' "\n\t')
    else:
      print fb.evaluateExpressionValue("[{} debugDescription]".format(element)).GetObjectDescription()


class FBXCPrintTree(fb.FBCommand):
  def name(self):
    return "xtree"

  def description(self):
    return "Print XCUIElement subtree."

  def args(self):
    return [fb.FBCommandArgument(arg="element", type="XCUIElement*", help="The element to print tree.", default="__default__")]

  def options(self):
    return [
      fb.FBCommandArgument(arg='pointer', short='-p', long='--pointer', type='BOOL', boolean=True, default=False, help='Print pointers'),
      fb.FBCommandArgument(arg='trait', short='-t', long='--traits', type='BOOL', boolean=True, default=False, help='Print traits'),
      fb.FBCommandArgument(arg='frame', short='-f', long='--frame', type='BOOL', boolean=True, default=False, help='Print frames')
    ]

  def run(self, arguments, options):
    element = arguments[0]
    language = fb.currentLanguage()
    if element == "__default__":
      element = "XCUIApplication()" if language == lldb.eLanguageTypeSwift else "(XCUIApplication *)[[XCUIApplication alloc] init]"

    # Evaluate object
    element_sbvalue = fb.evaluateExpressionValue("{}".format(element), language=language)
    """:type: lldb.SBValue"""

    # Get pointer value, so it will be working in Swift and Objective-C
    element_pointer = int(element_sbvalue.GetValue(), 16)

    # Get XCElementSnapshot object
    snapshot = take_snapshot(element_pointer)

    # Print tree for snapshot element
    snapshot_object = XCElementSnapshot(snapshot, language=language)
    print snapshot_object.tree().hierarchy_text(pointer=options.pointer, trait=options.trait, frame=options.frame)


class FBXCPrintObject(fb.FBCommand):
  def name(self):
    return "xobject"

  def description(self):
    return "Print XCUIElement details."

  def args(self):
    return [fb.FBCommandArgument(arg="element", type="XCUIElement*", help="The element to print details.", default="__default__")]

  def run(self, arguments, options):
    element = arguments[0]
    language = fb.currentLanguage()
    if element == "__default__":
      element = "XCUIApplication()" if language == lldb.eLanguageTypeSwift else "(XCUIApplication *)[[XCUIApplication alloc] init]"

    # Evaluate object
    element_sbvalue = fb.evaluateExpressionValue("{}".format(element), language=language)
    """:type: lldb.SBValue"""

    # Get pointer value, so it will be working in Swift and Objective-C
    element_pointer = int(element_sbvalue.GetValue(), 16)

    # Get XCElementSnapshot object
    snapshot = take_snapshot(element_pointer)

    # Print details of snapshot element
    snapshot_object = XCElementSnapshot(snapshot, language=language)
    print snapshot_object.detail_summary()


class FBXCNoId(fb.FBCommand):
  def name(self):
    return "xnoid"

  def description(self):
    return "Print XCUIElement objects with label but without identifier."

  def args(self):
    return [fb.FBCommandArgument(arg="element", type="XCUIElement*", help="The element from start to.", default="__default__")]

  def options(self):
    return [
      fb.FBCommandArgument(arg='status_bar', short='-s', long='--status-bar', type='BOOL', boolean=True, default=False, help='Print status bar items'),
      fb.FBCommandArgument(arg='pointer', short='-p', long='--pointer', type='BOOL', boolean=True, default=False, help='Print pointers'),
      fb.FBCommandArgument(arg='trait', short='-t', long='--traits', type='BOOL', boolean=True, default=False, help='Print traits'),
      fb.FBCommandArgument(arg='frame', short='-f', long='--frame', type='BOOL', boolean=True, default=False, help='Print frames')
    ]

  def run(self, arguments, options):
    element = arguments[0]
    language = fb.currentLanguage()
    if element == "__default__":
      element = "XCUIApplication()" if language == lldb.eLanguageTypeSwift else "(XCUIApplication *)[[XCUIApplication alloc] init]"

    # Evaluate object
    element_sbvalue = fb.evaluateExpressionValue("{}".format(element), language=language)
    """:type: lldb.SBValue"""

    # Get pointer value, so it will be working in Swift and Objective-C
    element_pointer = int(element_sbvalue.GetValue(), 16)

    # Get XCElementSnapshot object
    snapshot = take_snapshot(element_pointer)

    # Print tree for snapshot element
    snapshot_object = XCElementSnapshot(snapshot, language=language)
    elements = snapshot_object.find_missing_identifiers(status_bar=options.status_bar)
    if elements is not None:
      print elements.hierarchy_text(pointer=options.pointer, trait=options.trait, frame=options.frame)
    else:
      print "Couldn't found elements without identifier"


def take_snapshot(element):
  """
  Takes snapshot (XCElementSnapshot) from XCUIElement (as pointer)
  
  :param int element: Pointer to the XCUIElement
  :return: XCElementSnapshot object
  :rtype: lldb.SBValue
  """
  return fb.evaluateExpressionValue("(XCElementSnapshot *)[[[{} query] matchingSnapshotsWithError:nil] firstObject]".format(element))


class _ElementList(object):
  """
  Store element and list of children
  
  :param XCElementSnapshot element: XCElementSnapshot
  :param list[_ElementList] children: List of XCElementSnapshot objects
  """
  def __init__(self, element, children):
    self.element = element
    self.children = children

  def text(self, pointer, trait, frame, indent):
    """
    String representation of the element
    
    :param bool pointer: Print pointers
    :param bool trait: Print traits
    :param bool frame: Print frames
    :param int indent: Indention
    :return: String representation of the element
    :rtype: str
    """
    indent_string = ' | ' * indent
    return "{}{}\n".format(indent_string, self.element.summary(pointer=pointer, trait=trait, frame=frame))

  def hierarchy_text(self, pointer=False, trait=False, frame=False, indent=0):
    """
    String representation of the hierarchy of elements
    
    :param bool pointer: Print pointers
    :param bool trait: Print traits
    :param bool frame: Print frames
    :param int indent: Indention
    :return: String representation of the hierarchy of elements
    :rtype: str
    """
    s = self.text(pointer=pointer, trait=trait, frame=frame, indent=indent)
    for e in self.children:
      s += e.hierarchy_text(pointer=pointer, trait=trait, frame=frame, indent=indent+1)
    return s


class XCElementSnapshot(object):
  """
  XCElementSnapshot wrapper
  
  :param lldb.SBValue element: XCElementSnapshot object
  :param str element_value: Pointer to XCElementSnapshot object
  :param language: Project language
  :param lldb.SBValue _type: XCUIElement type / XCUIElementType
  :param lldb.SBValue _traits: UIAccessibilityTraits
  :param lldb.SBValue | None _frame: XCUIElement frame
  :param lldb.SBValue _identifier: XCUIElement identifier
  :param lldb.SBValue _value: XCUIElement value
  :param lldb.SBValue _placeholderValue: XCUIElement placeholder value
  :param lldb.SBValue _label: XCUIElement label
  :param lldb.SBValue _title: XCUIElement title
  :param lldb.SBValue _children: XCUIElement children
  :param lldb.SBValue _enabled: XCUIElement is enabled
  :param lldb.SBValue _selected: XCUIElement is selected
  :param lldb.SBValue _isMainWindow: XCUIElement is main window
  :param lldb.SBValue _hasKeyboardFocus: XCUIElement has keyboard focus
  :param lldb.SBValue _hasFocus: XCUIElement has focus
  :param lldb.SBValue _generation: XCUIElement generation
  :param lldb.SBValue _horizontalSizeClass: XCUIElement horizontal class
  :param lldb.SBValue _verticalSizeClass: XCUIElement vertical class
  """
  def __init__(self, element, language):
    """
    :param lldb.SBValue element: XCElementSnapshot object 
    :param language: Project language
    """
    super(XCElementSnapshot, self).__init__()
    self.element = element
    self.element_value = self.element.GetValue()
    self.language = language

    self._type = None
    self._traits = None
    self._frame = None
    self._identifier = None
    self._value = None
    self._placeholderValue = None
    self._label = None
    self._title = None
    self._children = None

    self._enabled = None
    self._selected = None
    self._isMainWindow = None
    self._hasKeyboardFocus = None
    self._hasFocus = None
    self._generation = None
    self._horizontalSizeClass = None
    self._verticalSizeClass = None

  @property
  def is_missing_identifier(self):
    """
    Checks if element has a label but doesn't have an identifier.
    
    :return: True if element has a label but doesn't have an identifier.
    :rtype: bool
    """
    return len(self.identifier_value) == 0 and len(self.label_value) > 0

  @property
  def type(self):
    """    
    :return: XCUIElement type / XCUIElementType
    :rtype: lldb.SBValue
    """
    if self._type is None:
      name = "_elementType"
      if self.element.GetIndexOfChildWithName(name) == NOT_FOUND:
        self._type = fb.evaluateExpressionValue("(int)[{} elementType]".format(self.element_value))
      else:
        self._type = self.element.GetChildMemberWithName(name)
    return self._type

  @property
  def type_value(self):
    """
    :return: XCUIElementType value
    :rtype: int
    """
    return int(self.type.GetValue())

  @property
  def type_summary(self):
    """
    :return: XCUIElementType summary
    :rtype: str
    """
    return self.get_type_value_string(self.type_value)

  @property
  def traits(self):
    """
    :return: UIAccessibilityTraits
    :rtype: lldb.SBValue
    """
    if self._traits is None:
      name = "_traits"
      if self.element.GetIndexOfChildWithName(name) == NOT_FOUND:
        self._traits = fb.evaluateExpressionValue("(int)[{} traits]".format(self.element_value))
      else:
        self._traits = self.element.GetChildMemberWithName(name)
    return self._traits

  @property
  def traits_value(self):
    """
    :return: UIAccessibilityTraits value
    :rtype: int
    """
    return int(self.traits.GetValue())

  @property
  def traits_summary(self):
    """
    :return: UIAccessibilityTraits summary
    :rtype: str
    """
    return self.get_traits_value_string(self.traits_value)

  @property
  def frame(self):
    """
    :return: XCUIElement frame
    :rtype: lldb.SBValue
    """
    if self._frame is None:
      import_uikit()
      name = "_frame"
      if self.element.GetIndexOfChildWithName(name) == NOT_FOUND:
        self._frame = fb.evaluateExpressionValue("(CGRect)[{} frame]".format(self.element_value))
      else:
        self._frame = self.element.GetChildMemberWithName(name)
    return self._frame

  @property
  def frame_summary(self):
    """
    :return: XCUIElement frame summary
    :rtype: str
    """
    return CGRect(self.frame).summary()

  @property
  def identifier(self):
    """
    :return: XCUIElement identifier
    :rtype: lldb.SBValue
    """
    if self._identifier is None:
      name = "_identifier"
      if self.element.GetIndexOfChildWithName(name) == NOT_FOUND:
        self._identifier = fb.evaluateExpressionValue("(NSString *)[{} identifier]".format(self.element_value))
      else:
        self._identifier = self.element.GetChildMemberWithName(name)
    return self._identifier

  @property
  def identifier_value(self):
    """
    :return: XCUIElement identifier value
    :rtype: str
    """
    return normalize_summary(self.identifier.GetSummary())

  @property
  def identifier_summary(self):
    """
    :return: XCUIElement identifier summary
    :rtype: str | None
    """
    if len(self.identifier_value) == 0:
      return None
    return "identifier: '{}'".format(self.identifier_value)

  @property
  def value(self):
    """
    :return: XCUIElement value
    :rtype: lldb.SBValue
    """
    if self._value is None:
      name = "_value"
      if self.element.GetIndexOfChildWithName(name) == NOT_FOUND:
        self._value = fb.evaluateExpressionValue("(NSString *)[{} value]".format(self.element_value))
      else:
        self._value = self.element.GetChildMemberWithName(name)
    return self._value

  @property
  def value_value(self):
    """
    :return: XCUIElement value value
    :rtype: str
    """
    return normalize_summary(self.value.GetSummary())

  @property
  def value_summary(self):
    """
    :return: XCUIElement value summary
    :rtype: str | None
    """
    if len(self.value_value) == 0:
      return None
    return "value: '{}'".format(self.value_value)

  @property
  def placeholder(self):
    """
    :return: XCUIElement placeholder value
    :rtype: lldb.SBValue
    """
    if self._placeholderValue is None:
      name = "_placeholderValue"
      if self.element.GetIndexOfChildWithName(name) == NOT_FOUND:
        self._placeholderValue = fb.evaluateExpressionValue("(NSString *)[{} placeholderValue]".format(self.element_value))
      else:
        self._placeholderValue = self.element.GetChildMemberWithName(name)
    return self._placeholderValue

  @property
  def placeholder_value(self):
    """
    :return: XCUIElement placeholderValue value
    :rtype: str
    """
    return normalize_summary(self.placeholder.GetSummary())

  @property
  def placeholder_summary(self):
    """
    :return: XCUIElement placeholderValue summary
    :rtype: str | None
    """
    if len(self.placeholder_value) == 0:
      return None
    return "placeholderValue: '{}'".format(self.placeholder_value)

  @property
  def label(self):
    """
    :return: XCUIElement label
    :rtype: lldb.SBValue
    """
    if self._label is None:
      name = "_label"
      if self.element.GetIndexOfChildWithName(name) == NOT_FOUND:
        self._label = fb.evaluateExpressionValue("(NSString *)[{} label]".format(self.element_value))
      else:
        self._label = self.element.GetChildMemberWithName(name)
    return self._label

  @property
  def label_value(self):
    """
    :return: XCUIElement label value
    :rtype: str
    """
    return normalize_summary(self.label.GetSummary())

  @property
  def label_summary(self):
    """
    :return: XCUIElement label summary
    :rtype: str | None
    """
    if len(self.label_value) == 0:
      return None
    return "label: '{}'".format(self.label_value)

  @property
  def title(self):
    """
    :return: XCUIElement title
    :rtype: lldb.SBValue
    """
    if self._title is None:
      name = "_title"
      if self.element.GetIndexOfChildWithName(name) == NOT_FOUND:
        self._title = fb.evaluateExpressionValue("(NSString *)[{} title]".format(self.element_value))
      else:
        self._title = self.element.GetChildMemberWithName(name)
    return self._title

  @property
  def title_value(self):
    """
    :return: XCUIElement title value
    :rtype: str
    """
    return normalize_summary(self.title.GetSummary())

  @property
  def title_summary(self):
    """
    :return: XCUIElement title summary
    :rtype: str | None
    """
    if len(self.title_value) == 0:
      return None
    return "title: '{}'".format(self.title_value)

  @property
  def children(self):
    """
    :return: XCUIElement children
    :rtype: lldb.SBValue
    """
    if self._children is None:
      name = "_children"
      if self.element.GetIndexOfChildWithName(name) == NOT_FOUND:
        self._children = fb.evaluateExpressionValue("(NSArray *)[{} children]".format(self.element_value))
      else:
        self._children = self.element.GetChildMemberWithName(name)
    return self._children

  @property
  def children_count(self):
    """
    :return: XCUIElement children count
    :rtype: int
    """
    return self.children.GetNumChildren()

  @property
  def children_list(self):
    """
    :return: XCUIElement children list
    :rtype: list[lldb.SBValue]
    """
    return [self.children.GetChildAtIndex(i) for i in xrange(0, self.children_count)]

  @property
  def enabled(self):
    """
    :return: XCUIElement is enabled
    :rtype: lldb.SBValue
    """
    if self._enabled is None:
      name = "_enabled"
      if self.element.GetIndexOfChildWithName(name) == NOT_FOUND:
        self._enabled = fb.evaluateExpressionValue("(BOOL)[{} enabled]".format(self.element_value))
      else:
        self._enabled = self.element.GetChildMemberWithName(name)
    return self._enabled

  @property
  def enabled_value(self):
    """
    :return: XCUIElement is enabled value
    :rtype: bool
    """
    return bool(self.enabled.GetValueAsSigned())

  @property
  def enabled_summary(self):
    """
    :return: XCUIElement is enabled summary
    :rtype: str | None
    """
    if not self.enabled_value:
      return "enabled: {}".format(self.enabled_value)
    return None

  @property
  def selected(self):
    """
    :return: XCUIElement is selected
    :rtype: lldb.SBValue
    """
    if self._selected is None:
      name = "_selected"
      if self.element.GetIndexOfChildWithName(name) == NOT_FOUND:
        self._selected = fb.evaluateExpressionValue("(BOOL)[{} selected]".format(self.element_value))
      else:
        self._selected = self.element.GetChildMemberWithName(name)
    return self._selected

  @property
  def selected_value(self):
    """
    :return: XCUIElement is selected value
    :rtype: bool
    """
    return bool(self.selected.GetValueAsSigned())

  @property
  def selected_summary(self):
    """
    :return: XCUIElement is selected summary
    :rtype: str | None
    """
    if self.selected_value:
      return "selected: {}".format(self.selected_value)
    return None

  @property
  def is_main_window(self):
    """
    :return: XCUIElement isMainWindow
    :rtype: lldb.SBValue
    """
    if self._isMainWindow is None:
      name = "_isMainWindow"
      if self.element.GetIndexOfChildWithName(name) == NOT_FOUND:
        self._isMainWindow = fb.evaluateExpressionValue("(BOOL)[{} isMainWindow]".format(self.element_value))
      else:
        self._isMainWindow = self.element.GetChildMemberWithName(name)
    return self._isMainWindow

  @property
  def is_main_window_value(self):
    """
    :return: XCUIElement isMainWindow value
    :rtype: bool
    """
    return bool(self.is_main_window.GetValueAsSigned())

  @property
  def is_main_window_summary(self):
    """
    :return: XCUIElement isMainWindow summary
    :rtype: str | None
    """
    if self.is_main_window_value:
      return "MainWindow"
    return None

  @property
  def keyboard_focus(self):
    """
    :return: XCUIElement hasKeyboardFocus
    :rtype: lldb.SBValue
    """
    if self._hasKeyboardFocus is None:
      name = "_hasKeyboardFocus"
      if self.element.GetIndexOfChildWithName(name) == NOT_FOUND:
        self._hasKeyboardFocus = fb.evaluateExpressionValue("(BOOL)[{} hasKeyboardFocus]".format(self.element_value))
      else:
        self._hasKeyboardFocus = self.element.GetChildMemberWithName(name)
    return self._hasKeyboardFocus

  @property
  def keyboard_focus_value(self):
    """
    :return: XCUIElement hasKeyboardFocus value
    :rtype: bool
    """
    return bool(self.keyboard_focus.GetValueAsSigned())

  @property
  def keyboard_focus_summary(self):
    """
    :return: XCUIElement hasKeyboardFocus summary
    :rtype: str | None
    """
    if self.keyboard_focus_value:
      return "hasKeyboardFocus: {}".format(self.keyboard_focus_value)
    return None

  @property
  def focus(self):
    """
    :return: XCUIElement hasFocus
    :rtype: lldb.SBValue
    """
    if self._hasFocus is None:
      name = "_hasFocus"
      if self.element.GetIndexOfChildWithName(name) == NOT_FOUND:
        self._hasFocus = fb.evaluateExpressionValue("(BOOL)[{} hasFocus]".format(self.element_value))
      else:
        self._hasFocus = self.element.GetChildMemberWithName(name)
    return self._hasFocus

  @property
  def focus_value(self):
    """
    :return: XCUIElement hasFocus value
    :rtype: bool
    """
    return bool(self.focus.GetValueAsSigned())

  @property
  def focus_summary(self):
    """
    :return: XCUIElement hasFocus summary
    :rtype: str | None
    """
    if self.focus_value:
      return "hasFocus: {}".format(self.focus_value)
    return None

  @property
  def generation(self):
    """
    :return: XCUIElement generation
    :rtype: lldb.SBValue
    """
    if self._generation is None:
      name = "_generation"
      if self.element.GetIndexOfChildWithName(name) == NOT_FOUND:
        self._generation = fb.evaluateExpressionValue("(unsigned int)[{} generation]".format(self.element_value))
      else:
        self._generation = self.element.GetChildMemberWithName(name)
    return self._generation

  @property
  def generation_value(self):
    """
    :return: XCUIElement generation value
    :rtype: int 
    """
    return int(self.generation.GetValueAsUnsigned())

  @property
  def horizontal_size_class(self):
    """
    :return: XCUIElement horizontal size class
    :rtype: lldb.SBValue
    """
    if self._horizontalSizeClass is None:
      name = "_horizontalSizeClass"
      if self.element.GetIndexOfChildWithName(name) == NOT_FOUND:
        self._horizontalSizeClass = fb.evaluateExpressionValue("(int)[{} horizontalSizeClass]".format(self.element_value))
      else:
        self._horizontalSizeClass = self.element.GetChildMemberWithName(name)
    return self._horizontalSizeClass

  @property
  def horizontal_size_class_value(self):
    """
    :return: XCUIElement horizontal size class value
    :rtype: int
    """
    return int(self.horizontal_size_class.GetValue())

  @property
  def horizontal_size_class_summary(self):
    """
    :return:  XCUIElement horizontal size class summary
    """
    return self.get_user_interface_size_class_string(self.horizontal_size_class_value)

  @property
  def vertical_size_class(self):
    """
    :return: XCUIElement vertical size class
    :rtype: lldb.SBValue
    """
    if self._verticalSizeClass is None:
      name = "_verticalSizeClass"
      if self.element.GetIndexOfChildWithName(name) == NOT_FOUND:
        self._verticalSizeClass = fb.evaluateExpressionValue("(int)[{} verticalSizeClass]".format(self.element_value))
      else:
        self._verticalSizeClass = self.element.GetChildMemberWithName(name)
    return self._verticalSizeClass

  @property
  def vertical_size_class_value(self):
    """
    :return: XCUIElement vertical size class value
    :rtype: int
    """
    return int(self.vertical_size_class.GetValue())

  @property
  def vertical_size_class_summary(self):
    """
    :return:  XCUIElement vertical size class summary
    """
    return self.get_user_interface_size_class_string(self.vertical_size_class_value)

  @property
  def uniquely_identifying_objective_c_code(self):
    """
    :return: XCUIElement uniquely identifying Objective-C code
    :rtype: lldb.SBValue
    """
    return fb.evaluateExpressionValue("(id)[{} _uniquelyIdentifyingObjectiveCCode]".format(self.element_value))

  @property
  def uniquely_identifying_objective_c_code_value(self):
    """
    :return: XCUIElement uniquely identifying Objective-C code value
    :rtype: str
    """
    return normalize_array_description(self.uniquely_identifying_objective_c_code.GetObjectDescription())

  @property
  def uniquely_identifying_swift_code(self):
    """
    :return: XCUIElement uniquely identifying Swift code
    :rtype: lldb.SBValue
    """
    return fb.evaluateExpressionValue("(id)[{} _uniquelyIdentifyingSwiftCode]".format(self.element_value))

  @property
  def uniquely_identifying_swift_code_value(self):
    """
    :return: XCUIElement uniquely identifying Swift code value
    :rtype: str
    """
    return normalize_array_description(self.uniquely_identifying_swift_code.GetObjectDescription())

  @property
  def is_touch_bar_element(self):
    """
    :return: XCUIElement is touch bar element
    :rtype: lldb.SBValue
    """
    return fb.evaluateExpressionValue("(BOOL)[{} isTouchBarElement]".format(self.element_value))

  @property
  def is_touch_bar_element_value(self):
    """
    :return: XCUIElement is touch bar element value
    :rtype: bool
    """
    return bool(self.is_touch_bar_element.GetValueAsSigned())

  @property
  def is_top_level_touch_bar_element(self):
    """
    :return: XCUIElement is top level touch bar element
    :rtype: lldb.SBValue
    """
    return fb.evaluateExpressionValue("(BOOL)[{} isTopLevelTouchBarElement]".format(self.element_value))

  @property
  def is_top_level_touch_bar_element_value(self):
    """
    :return: XCUIElement is top level touch bar element value
    :rtype: bool
    """
    return bool(self.is_top_level_touch_bar_element.GetValueAsSigned())

  @property
  def suggested_hit_points(self):
    """
    :return: XCUIElement suggested hit points
    :rtype: lldb.SBValue
    """
    return fb.evaluateExpressionValue("(NSArray *)[{} suggestedHitpoints]".format(self.element_value))

  @property
  def suggested_hit_points_value(self):
    """
    :return: XCUIElement suggested hit points
    :rtype: str
    """
    return normalize_array_description(self.suggested_hit_points.GetObjectDescription())

  @property
  def visible_frame(self):
    """
    :return: XCUIElement visible frame
    :rtype: lldb.SBValue
    """
    import_uikit()
    return fb.evaluateExpressionValue("(CGRect)[{} visibleFrame]".format(self.element_value))

  @property
  def visible_frame_summary(self):
    """
    :return: XCUIElement visible frame
    :rtype: str
    """
    return CGRect(self.visible_frame).summary()

  @property
  def depth(self):
    """
    :return: XCUIElement depth
    :rtype: lldb.SBValue
    """
    return fb.evaluateExpressionValue("(int)[{} depth]".format(self.element_value))

  @property
  def depth_value(self):
    """
    :return: XCUIElement depth
    :rtype: int 
    """
    return int(self.depth.GetValue())

  @property
  def hit_point(self):
    """
    :return: XCUIElement hit point
    :rtype: lldb.SBValue
    """
    import_uikit()
    return fb.evaluateExpressionValue("(CGPoint)[{} hitPoint]".format(self.element_value))

  @property
  def hit_point_value(self):
    """
    :return: XCUIElement hit point
    :rtype: str
    """
    return CGPoint(self.hit_point).summary()

  @property
  def hit_point_for_scrolling(self):
    """
    :return: XCUIElement hit point for scrolling
    :rtype: lldb.SBValue
    """
    import_uikit()
    return fb.evaluateExpressionValue("(CGPoint)[{} hitPointForScrolling]".format(self.element_value))

  @property
  def hit_point_for_scrolling_value(self):
    """
    :return: XCUIElement hit point for scrolling
    :rtype: str
    """
    return CGPoint(self.hit_point_for_scrolling).summary()

  def summary(self, pointer=False, trait=False, frame=False):
    """
    Returns XCElementSnapshot summary
    
    :param bool pointer: Print pointers
    :param bool trait: Print traits
    :param bool frame: Print frames
    :return: XCElementSnapshot summary
    :rtype: str
    """
    type_text = self.type_summary
    if pointer:
      type_text += " {:#x}".format(int(self.element_value, 16))
    if trait:
      type_text += " traits: {}({:#x})".format(self.traits_summary, self.traits_value)

    frame_text = self.frame_summary if frame else None
    identifier = self.identifier_summary
    label = self.label_summary
    title = self.title_summary
    value = self.value_summary
    placeholder = self.placeholder_summary
    enabled = self.enabled_summary
    selected = self.selected_summary
    main_window = self.is_main_window_summary
    keyboard_focus = self.keyboard_focus_summary
    focus = self.focus_summary

    texts = [t for t in
             [frame_text, identifier, label, title, value, placeholder,
              enabled, selected, main_window, keyboard_focus, focus]
             if t is not None]

    return "{}: {}".format(type_text, ", ".join(texts))

  def detail_summary(self):
    """
    Returns XCElementSnapshot detail summary
    
    :return: XCElementSnapshot detail summary
    :rtype: str
    """
    texts = list()
    texts.append("Pointer: {:#x}".format(int(self.element_value, 16)))
    texts.append("Type: {}".format(self.type_summary))
    texts.append("Depth: {}".format(self.depth_value))
    texts.append("Traits: {} ({:#x})".format(self.traits_summary, self.traits_value))
    texts.append("Frame: {}".format(self.frame_summary))
    texts.append("Visible frame: {}".format(self.visible_frame_summary))
    texts.append("Identifier: '{}'".format(self.identifier_value))
    texts.append("Label: '{}'".format(self.label_value))
    texts.append("Title: '{}'".format(self.title_value))
    texts.append("Value: '{}'".format(self.value_value))
    texts.append("Placeholder: '{}'".format(self.placeholder_value))
    if self.language != lldb.eLanguageTypeSwift:
      # They doesn't work on Swift :(
      texts.append("Hit point: {}".format(self.hit_point_value))
      texts.append("Hit point for scrolling: {}".format(self.hit_point_for_scrolling_value))
    texts.append("Enabled: {}".format(self.enabled_value))
    texts.append("Selected: {}".format(self.selected_value))
    texts.append("Main Window: {}".format(self.is_main_window_value))
    texts.append("Keyboard focus: {}".format(self.keyboard_focus_value))
    texts.append("Focus: {}".format(self.focus_value))
    texts.append("Generation: {}".format(self.generation_value))
    texts.append("Horizontal size class: {}".format(self.horizontal_size_class_summary))
    texts.append("Vertical size class: {}".format(self.vertical_size_class_summary))
    texts.append("TouchBar element: {}".format(self.is_touch_bar_element_value))
    texts.append("TouchBar top level element: {}".format(self.is_top_level_touch_bar_element_value))
    texts.append("Unique Objective-C: {}".format(self.uniquely_identifying_objective_c_code_value))
    texts.append("Unique Swift: {}".format(self.uniquely_identifying_swift_code_value))
    texts.append("Suggested hit points: {}".format(self.suggested_hit_points_value))
    return "\n".join(texts)

  def tree(self):
    """
    Returns tree of elements in hierarchy
    
    :return: Elements hierarchy
    :rtype: _ElementList
    """
    children = [XCElementSnapshot(e, self.language).tree() for e in self.children_list]
    return _ElementList(self, children)

  def find_missing_identifiers(self, status_bar):
    """
    Find element which has a label but doesn't have an identifier
     
    :param bool status_bar: Print status bar items
    :return: Hierarchy structure with items which has a label but doesn't have an identifier
    :rtype: _ElementList | None
    """
    # Do not print status bar items
    if status_bar is not True and self.type_value == XCUIElementType.StatusBar:
      return None

    children_missing = [XCElementSnapshot(e, self.language).find_missing_identifiers(status_bar=status_bar) for e in self.children_list]
    children_missing = [x for x in children_missing if x is not None]

    # Self and its children are not missing identifiers
    if self.is_missing_identifier is False and len(children_missing) == 0:
      return None

    return _ElementList(self, children_missing)

  @staticmethod
  def get_type_value_string(value):
    """
    Get element type string from XCUIElementType (as int)
    
    :param int value: XCUIElementType (as int)
    :return: XCUIElementType string
    :rtype: str
    """
    return XCUIElementType.name_for_value(value)

  @staticmethod
  def get_traits_value_string(value):
    """
    Get element traits string from UIAccessibilityTraits (as int)
    
    :param int value: UIAccessibilityTraits (as int)
    :return: UIAccessibilityTraits string
    :rtype: str
    """
    return UIAccessibilityTraits.name_for_value(value)

  @staticmethod
  def get_user_interface_size_class_string(value):
    """
    Get user interface size class string from UIUserInterfaceSizeClass (as int)
    
    :param value: UIAccessibilityTraits (as int)
    :return: UIUserInterfaceSizeClass string
    :rtype: str
    """
    return UIUserInterfaceSizeClass.name_for_value(value)


class XCUIElementType(object):
  """
  Represents all XCUIElementType types
  """
  Any = 0
  Other = 1
  Application = 2
  Group = 3
  Window = 4
  Sheet = 5
  Drawer = 6
  Alert = 7
  Dialog = 8
  Button = 9
  RadioButton = 10
  RadioGroup = 11
  CheckBox = 12
  DisclosureTriangle = 13
  PopUpButton = 14
  ComboBox = 15
  MenuButton = 16
  ToolbarButton = 17
  Popover = 18
  Keyboard = 19
  Key = 20
  NavigationBar = 21
  TabBar = 22
  TabGroup = 23
  Toolbar = 24
  StatusBar = 25
  Table = 26
  TableRow = 27
  TableColumn = 28
  Outline = 29
  OutlineRow = 30
  Browser = 31
  CollectionView = 32
  Slider = 33
  PageIndicator = 34
  ProgressIndicator = 35
  ActivityIndicator = 36
  SegmentedControl = 37
  Picker = 38
  PickerWheel = 39
  Switch = 40
  Toggle = 41
  Link = 42
  Image = 43
  Icon = 44
  SearchField = 45
  ScrollView = 46
  ScrollBar = 47
  StaticText = 48
  TextField = 49
  SecureTextField = 50
  DatePicker = 51
  TextView = 52
  Menu = 53
  MenuItem = 54
  MenuBar = 55
  MenuBarItem = 56
  Map = 57
  WebView = 58
  IncrementArrow = 59
  DecrementArrow = 60
  Timeline = 61
  RatingIndicator = 62
  ValueIndicator = 63
  SplitGroup = 64
  Splitter = 65
  RelevanceIndicator = 66
  ColorWell = 67
  HelpTag = 68
  Matte = 69
  DockItem = 70
  Ruler = 71
  RulerMarker = 72
  Grid = 73
  LevelIndicator = 74
  Cell = 75
  LayoutArea = 76
  LayoutItem = 77
  Handle = 78
  Stepper = 79
  Tab = 80
  TouchBar = 81

  @classmethod
  def _attributes_by_value(cls):
    """
    :return: Hash of all attributes and their values 
    :rtype: dict[int, str]
    """
    class_attributes = set(dir(cls)) - set(dir(object))
    return dict([(getattr(cls, n), n) for n in class_attributes if not callable(getattr(cls, n)) and not n.startswith("__")])

  @classmethod
  def name_for_value(cls, value):
    """
    Get element type string from XCUIElementType (as int)
    
    :param int value: XCUIElementType (as int)
    :return: Name of type
    :rtype: str
    """
    attributes = cls._attributes_by_value()
    if value in attributes:
      return attributes[value]
    else:
      return "Unknown ({:#x})".format(value)


class UIAccessibilityTraits(object):
  """
  Represents all UIAccessibilityTraits types
  """
  Button = 0x0000000000000001
  Link = 0x0000000000000002
  Image = 0x0000000000000004
  Selected = 0x0000000000000008
  PlaysSound = 0x0000000000000010
  KeyboardKey = 0x0000000000000020
  StaticText = 0x0000000000000040
  SummaryElement = 0x0000000000000080
  NotEnabled = 0x0000000000000100
  UpdatesFrequently = 0x0000000000000200
  SearchField = 0x0000000000000400
  StartsMediaSession = 0x0000000000000800
  Adjustable = 0x0000000000001000
  AllowsDirectInteraction = 0x0000000000002000
  CausesPageTurn = 0x0000000000004000
  TabBar = 0x0000000000008000
  Header = 0x0000000000010000

  @classmethod
  def _attributes_by_value(cls):
    """
    :return: Hash of all attributes and their values 
    :rtype: dict[int, str]
    """
    class_attributes = set(dir(cls)) - set(dir(object))
    return dict([(getattr(cls, n), n) for n in class_attributes if not callable(getattr(cls, n)) and not n.startswith("__")])

  @classmethod
  def name_for_value(cls, value):
    """
    Get element traits string from UIAccessibilityTraits (as int)

    :param int value: UIAccessibilityTraits (as int)
    :return: UIAccessibilityTraits string
    :rtype: str
    """
    if value == 0:
      return "None"

    traits = []
    attributes = cls._attributes_by_value()
    for k in attributes.keys():
      if value & k:
        traits.append(attributes[k])

    if len(traits) == 0:
      return "Unknown"
    else:
      return ", ".join(traits)


class UIUserInterfaceSizeClass(object):
  """
  Represents all UIUserInterfaceSizeClass types
  """
  Unspecified = 0
  Compact = 1
  Regular = 2

  @classmethod
  def name_for_value(cls, value):
    """
    Get user interface size class string from UIUserInterfaceSizeClass (as int)
    
    :param int value: UIAccessibilityTraits (as int)
    :return: UIUserInterfaceSizeClass string
    :rtype: str
    """
    if value == cls.Unspecified:
      return "Unspecified"
    elif value == cls.Compact:
      return "Compact"
    elif value == cls.Regular:
      return "Regular"
    else:
      return "Unknown ({:#x})".format(value)


class CGRect(object):
  """
  CGRect wrapper
  
  :param lldb.SBValue element: CGRect object
  """

  def __init__(self, element):
    """
    :param lldb.SBValue element: CGRect object  
    """
    super(CGRect, self).__init__()

    self.element = element

  def summary(self):
    """
    :return: CGRect summary
    :rtype: str
    """
    origin_element = self.element.GetChildMemberWithName("origin")
    origin = CGPoint(origin_element)

    size = self.element.GetChildMemberWithName("size")
    width = size.GetChildMemberWithName("width")
    height = size.GetChildMemberWithName("height")

    width_value = float(width.GetValue())
    height_value = float(height.GetValue())
    return "{{{}, {{{}, {}}}}}".format(origin.summary(), width_value, height_value)


class CGPoint(object):
  """
  CGPoint wrapper
  
  :param lldb.SBValue element: CGPoint object
  """

  def __init__(self, element):
    super(CGPoint, self).__init__()

    self.element = element

  def summary(self):
    """
    :return: CGPoint summary
    :rtype: str
    """
    x = self.element.GetChildMemberWithName("x")
    y = self.element.GetChildMemberWithName("y")

    x_value = float(x.GetValue())
    y_value = float(y.GetValue())
    return "{{{}, {}}}".format(x_value, y_value)


def normalize_summary(summary):
  """
  Normalize summary by removing "'" and "@" characters
  
  :param str summary: Summary string to normalize 
  :return: Normalized summary string
  :rtype: str
  """
  return summary \
    .lstrip("@") \
    .strip("\"")


def normalize_array_description(description):
  """
  Normalize array object description by removing "<" and ">" characters and content between them.
  
  :param str description: Array object description 
  :return: Normalized array object description string
  :rtype: str
  """
  return re.sub("^(<.*>)", "", description).strip()


_uikit_imported = False
def import_uikit():
  """
  Import UIKit framework to the debugger
  """
  global _uikit_imported
  if _uikit_imported:
    return
  _uikit_imported = True
  fb.evaluateExpressionValue("@import UIKit")


def debug(element):
  """
  Debug helper
  
  :param lldb.SBValue element: Element to debug 
  """
  print("---")
  print("element: {}".format(element))
  print("element class: {}".format(element.__class__))
  print("element name: {}".format(element.GetName()))
  print("element type name: {}".format(element.GetTypeName()))
  print("element value: {}".format(element.GetValue()))
  print("element value class: {}".format(element.GetValue().__class__))
  print("element value type: {}".format(element.GetValueType()))
  print("element value signed: {0}({0:#x})".format(element.GetValueAsSigned()))
  print("element value unsigned: {0}({0:#x})".format(element.GetValueAsUnsigned()))
  print("element summary: {}".format(element.GetSummary()))
  print("element description: {}".format(element.GetObjectDescription()))
  print("element children num: {}".format(element.GetNumChildren()))
  for i in range(0, element.GetNumChildren()):
    child = element.GetChildAtIndex(i)
    """:type: lldb.SBValue"""
    print("element child {:02}: {}".format(i, child.GetName()))
  print("===")
