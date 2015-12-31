#!/usr/bin/python
# Example file with custom commands, located at /magical/commands/example.py

import lldb
import fblldbbase as fb
import fblldbviewhelpers as viewHelpers
import fblldbobjecthelpers as objcHelpers

def lldbcommands():
  return [ 
    FBPrintWhyViewNotVisible(),
    FBPrintWhyViewNotInteractable(),
  ]

class FBPrintWhyViewNotVisible(fb.FBCommand):
  def name(self):
    return 'wnvisible'

  def description(self):
    return 'Print the reasons the given view is not visible.'

  def args(self):
    return [ fb.FBCommandArgument(arg='aView', type='UIView/NSView *', help='The view to check why it isn\'t visible.') ]

  def run(self, arguments, options):
    view = arguments[0]

    if not viewHelpers.isView(view):
      print 'Argument is not a view\n'
      return

    reasons = ''

    # width or height is 0
    size = '((CGRect)[(id)' + view + ' frame]).size'
    width = float(fb.evaluateExpression(size + '.width'))
    height = float(fb.evaluateExpression(size + '.height'))
    if width == 0.0 or height == 0.0:
      reasons += 'The width or height is 0. Did you forget to set the frame?\n'

    # view is out of bounds of its superview
    origin = '((CGRect)[(id)' + view + ' frame]).origin'
    xValue = float(fb.evaluateExpression(origin + '.x'))
    yValue = float(fb.evaluateExpression(origin + '.y'))
    if xValue < 0.0 or yValue < 0.0:
      reasons += 'The x or y values are smaller than 0\n'

    # view is hidden
    isHidden = fb.evaluateBooleanExpression('[' + view + ' isHidden]')
    if isHidden:
      reasons += 'View\'s hidden property is YES\n'

    # alpha is 0
    alpha = float(fb.evaluateExpression('(CGFloat)[' + view + ' alpha]'))
    if alpha == 0.0:
      reasons += 'View\'s alpha property is 0\n'

    # view wasn't added to the view hierarchy, or added to a view hierarchy who's not on the screen
    superview = self.superviewOfView(view)
    window = self.windowOfView(view)
    if not superview:
      reasons += 'View''s superview is nil. Did you forget to call addSubview?\n'
    elif not window:
      reasons += 'View is not in the view hierarchy\n'

    # view has a clear background and no subviews
    hasClearBackground = fb.evaluateBooleanExpression('(id)[' + view + ' backgroundColor] == nil || '
      '(BOOL)[(id)[' + view + ' backgroundColor] isEqual:[UIColor clearColor]]')
    numberOfSubviews = self.numberOfSubviews(view)
    if hasClearBackground:
      if numberOfSubviews == 0:
        reasons += 'View has a clear background and no subviews.\n'
      else:
        reasons += 'View has a clear background.\n'

    # view's background color is equal to its superview's
    hasSameBackgroundColor = fb.evaluateBooleanExpression('[[' + view + ' backgroundColor] isEqual:(id)[[' + view + ' superview] backgroundColor]]')
    if hasSameBackgroundColor:
      reasons += 'View\'s background color is equal to superview\'s background color\n'

    # view hidden behind the navigation bar
    vc = self.owningViewController(view)
    if vc:
      topLayoutGuide = float(fb.evaluateExpression('(CGFloat)[(id)[' + vc + ' topLayoutGuide] length]'))
      maxY = yValue + height
      if maxY < topLayoutGuide:
        reasons += 'View might be hidden behind the navigation bar\n'

    if reasons == '':
      reasons = 'No idea\n'

    print reasons

  def subviewsOfView(self, view):
    return fb.evaluateObjectExpression('[' + view + ' subviews]')

  def numberOfSubviews(self, view):
    return fb.evaluateIntegerExpression('[(id)' + self.subviewsOfView(view) + ' count]')

  def superviewOfView(self, view):
    superview = fb.evaluateObjectExpression('[' + view + ' superview]')
    if self.isNil(view):
      return None

    return superview

  def windowOfView(self, view):
    window = fb.evaluateObjectExpression('[' + view + ' window]')
    if self.isNil(window):
      return None

    return window

  def isNil(self, object):
    return int(object, 16) == 0

  def owningViewController(self, obj):
    while obj:
      if self.isViewController(obj):
        return obj
      else:
        obj = self.nextResponder(obj)

    return None

  def isViewController(self, obj):
    return objcHelpers.isKindOfClass('(' + obj + ')', 'UIViewController')

  def nextResponder(self, obj):
    aNextResponder = fb.evaluateObjectExpression('[((id){}) nextResponder]'.format(obj))
    try:
      if int(aNextResponder, 0):
        return aNextResponder
      else:
        return None
    except:
      return None


class FBPrintWhyViewNotInteractable(fb.FBCommand):
  def name(self):
    return 'wninteractable'

  def description(self):
    return 'Print the reasons the given view is not interactable.'

  def args(self):
    return [ fb.FBCommandArgument(arg='aView', type='UIView/NSView *', help='The view to check why it isn\'t interactable.') ]

  def run(self, arguments, options):
    view = arguments[0]

    if not viewHelpers.isView(view):
      print 'Argument is not a view\n'
      return

    reasons = ''

    # view's userInteractionEnabled is false
    isUserInteractionEnabled = fb.evaluateBooleanExpression('[' + view + ' isUserInteractionEnabled]')
    if not isUserInteractionEnabled:
      reasons += 'View\'s userInteractionEnabled property is NO\n'

    isUIControl = objcHelpers.isKindOfClass('(' + view + ')', 'UIControl')
    if isUIControl:
      # view's isEnabled property is false
      isEnabled = fb.evaluateBooleanExpression('[' + view + ' isEnabled]')
      if not isEnabled:
        reasons += 'View\'s isEnabled property is NO\n'

      # no target/action pairs
      numberOfEvents = fb.evaluateIntegerExpression('[' + view + ' allControlEvents]')
      if numberOfEvents == 0:
        reasons += 'No target/action pairs have been added to this control\n'

    if reasons == '':
      reasons = 'No idea\n'

    print reasons
