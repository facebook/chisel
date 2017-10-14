/**
 * Copyright (c) 2016-present, Facebook, Inc.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree. An additional grant
 * of patent rights can be found in the PATENTS file in the same directory.
 */

#import <Foundation/Foundation.h>

#import "FBObjectiveCGraphElement.h"

@class FBGraphEdgeFilterProvider;

/**
 FBObjectiveCGraphElement specialization that can gather all references kept in ivars, as part of collection
 etc.
 */
@interface FBObjectiveCObject : FBObjectiveCGraphElement
@end
