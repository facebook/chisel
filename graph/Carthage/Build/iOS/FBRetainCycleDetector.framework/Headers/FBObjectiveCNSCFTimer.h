/**
 * Copyright (c) 2016-present, Facebook, Inc.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree. An additional grant
 * of patent rights can be found in the PATENTS file in the same directory.
 */

#import <Foundation/Foundation.h>

#import "FBObjectiveCObject.h"

/**
 Specialization of FBObjectiveCObject for NSTimer.
 Standard methods that FBObjectiveCObject uses will not fetch us all objects retained by NSTimer.
 One good example is target of NSTimer.
 */
@interface FBObjectiveCNSCFTimer : FBObjectiveCObject
@end
