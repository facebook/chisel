/**
 * Copyright (c) 2016-present, Facebook, Inc.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree. An additional grant
 * of patent rights can be found in the PATENTS file in the same directory.
 */

#import <UIKit/UIKit.h>
#import <XCTest/XCTest.h>

#import <FBRetainCycleDetector/FBObjectiveCBlock.h>
#import <FBRetainCycleDetector/FBObjectiveCGraphElement+Internal.h>
#import <FBRetainCycleDetector/FBObjectiveCNSCFTimer.h>
#import <FBRetainCycleDetector/FBObjectiveCObject.h>
#import <FBRetainCycleDetector/FBRetainCycleDetector+Internal.h>

@interface _RCDTestTimer : NSObject
@property (nonatomic, strong) NSTimer *timer;
@end
@implementation _RCDTestTimer
@end

@interface FBObjectiveCNSCFTimerTests : XCTestCase
@end

@implementation FBObjectiveCNSCFTimerTests

#if _INTERNAL_RCD_ENABLED

- (void)testThatNSTimerCreatesRetainCycleAndWillBeDetected
{
  _RCDTestTimer *testObject = [_RCDTestTimer new];
  testObject.timer = [NSTimer scheduledTimerWithTimeInterval:DISPATCH_TIME_FOREVER
                                                      target:testObject
                                                    selector:@selector(description)
                                                    userInfo:nil
                                                     repeats:NO];

  FBRetainCycleDetector *detector = [FBRetainCycleDetector new];
  [detector addCandidate:testObject];
  NSSet *retainCycles = [detector findRetainCycles];

  NSSet *expectedCycle = [NSSet setWithObject:[detector _shiftToUnifiedCycle:
                                               @[[[FBObjectiveCObject alloc] initWithObject:testObject],
                                                 [[FBObjectiveCNSCFTimer alloc] initWithObject:testObject.timer]]]];

  XCTAssertEqualObjects(retainCycles, expectedCycle);
}

- (void)testThatNSTimerCreatesRetainCycleButWillBeSkippedIfDetectorIsConfiguredToSkip
{
  _RCDTestTimer *testObject = [_RCDTestTimer new];
  testObject.timer = [NSTimer scheduledTimerWithTimeInterval:DISPATCH_TIME_FOREVER
                                                      target:testObject
                                                    selector:@selector(description)
                                                    userInfo:nil
                                                     repeats:NO];

  FBObjectGraphConfiguration *configuration =
  [[FBObjectGraphConfiguration alloc] initWithFilterBlocks:@[]
                                       shouldInspectTimers:NO];
  
  FBRetainCycleDetector *detector = [[FBRetainCycleDetector alloc] initWithConfiguration:configuration];
  
  [detector addCandidate:testObject];
  NSSet *retainCycles = [detector findRetainCycles];

  XCTAssertEqual([retainCycles count], 0);
}

#endif //_INTERNAL_RCD_ENABLED

@end
