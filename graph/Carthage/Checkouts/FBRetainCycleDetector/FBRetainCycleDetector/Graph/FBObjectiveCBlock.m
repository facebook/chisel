/**
 * Copyright (c) 2016-present, Facebook, Inc.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree. An additional grant
 * of patent rights can be found in the PATENTS file in the same directory.
 */

#import "FBObjectiveCBlock.h"

#import <objc/runtime.h>

#import "FBBlockStrongLayout.h"
#import "FBObjectiveCObject.h"
#import "FBRetainCycleUtils.h"

@implementation FBObjectiveCBlock

- (NSSet *)allRetainedObjects
{
  NSMutableArray *results = [[[super allRetainedObjects] allObjects] mutableCopy];

  // Grab a strong reference to the object, otherwise it can crash while doing
  // nasty stuff on deallocation
  __attribute__((objc_precise_lifetime)) id anObject = self.object;

  void *blockObjectReference = (__bridge void *)anObject;
  NSArray *allRetainedReferences = FBGetBlockStrongReferences(blockObjectReference);

  for (id object in allRetainedReferences) {
    FBObjectiveCGraphElement *element = FBWrapObjectGraphElement(self, object, self.configuration);
    if (element) {
      [results addObject:element];
    }
  }

  return [NSSet setWithArray:results];
}

@end
