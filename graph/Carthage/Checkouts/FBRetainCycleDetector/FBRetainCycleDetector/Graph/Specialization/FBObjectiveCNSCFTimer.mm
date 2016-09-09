/**
 * Copyright (c) 2016-present, Facebook, Inc.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree. An additional grant
 * of patent rights can be found in the PATENTS file in the same directory.
 */

#import "FBObjectiveCNSCFTimer.h"

#import <objc/runtime.h>

#import "FBRetainCycleDetector.h"
#import "FBRetainCycleUtils.h"

@implementation FBObjectiveCNSCFTimer

#if _INTERNAL_RCD_ENABLED

typedef struct {
  long _unknown; // This is always 1
  id target;
  SEL selector;
  NSDictionary *userInfo;
} _FBNSCFTimerInfoStruct;

- (NSSet *)allRetainedObjects
{
  // Let's retain our timer
  __attribute__((objc_precise_lifetime)) NSTimer *timer = self.object;

  if (!timer) {
    return nil;
  }

  NSMutableSet *retained = [[super allRetainedObjects] mutableCopy];

  CFRunLoopTimerContext context;
  CFRunLoopTimerGetContext((CFRunLoopTimerRef)timer, &context);

  // If it has a retain function, let's assume it retains strongly
  if (context.info && context.retain) {
    _FBNSCFTimerInfoStruct infoStruct = *(_FBNSCFTimerInfoStruct *)(context.info);
    if (infoStruct.target) {
      FBObjectiveCGraphElement *element = FBWrapObjectGraphElementWithContext(self, infoStruct.target, self.configuration, @[@"target"]);
      if (element) {
        [retained addObject:element];
      }
    }
    if (infoStruct.userInfo) {
      FBObjectiveCGraphElement *element = FBWrapObjectGraphElementWithContext(self, infoStruct.userInfo, self.configuration, @[@"userInfo"]);
      if (element) {
        [retained addObject:element];
      }
    }
  }

  return retained;
}

#endif // _INTERNAL_RCD_ENABLED

@end
