/**
 * Copyright (c) 2016-present, Facebook, Inc.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree. An additional grant
 * of patent rights can be found in the PATENTS file in the same directory.
 */

#import <XCTest/XCTest.h>

#import <FBRetainCycleDetector/FBObjectiveCGraphElement+Internal.h>
#import <FBRetainCycleDetector/FBObjectiveCObject.h>
#import <FBRetainCycleDetector/FBRetainCycleDetector.h>
#import <FBRetainCycleDetector/FBStandardGraphEdgeFilters.h>

@interface FBGraphEdgeFilterTestClass: NSObject
@property (nonatomic, strong) NSObject *filtered;
@property (nonatomic, strong) NSObject *filtered2;
@end
@implementation FBGraphEdgeFilterTestClass
@end

@interface FBGraphEdgeFilterTests : XCTestCase
@end

@implementation FBGraphEdgeFilterTests

#if _INTERNAL_RCD_ENABLED

- (void)testIfApplyingEmptyFilterWillNotAlterResults
{
  FBGraphEdgeFilterTestClass *testObject = [FBGraphEdgeFilterTestClass new];
  testObject.filtered = testObject;

  FBRetainCycleDetector *detector = [FBRetainCycleDetector new];
  [detector addCandidate:testObject];

  NSSet *retainCycles = [detector findRetainCycles];

  NSSet *expectedCycles = [NSSet setWithObject:@[[[FBObjectiveCObject alloc] initWithObject:testObject]]];

  XCTAssertEqualObjects(retainCycles, expectedCycles);
}

- (void)testIfApplyingFilterForOnePropertyWillFilterOutThatProperty
{
  FBGraphEdgeFilterTestClass *testObject = [FBGraphEdgeFilterTestClass new];
  testObject.filtered = testObject;
  
  NSArray *filterBlocks = @[FBFilterBlockWithObjectIvarRelation([FBGraphEdgeFilterTestClass class],
                                                                @"_filtered")];
  FBObjectGraphConfiguration *configuration =
  [[FBObjectGraphConfiguration alloc] initWithFilterBlocks:filterBlocks
                                       shouldInspectTimers:YES];

  FBRetainCycleDetector *detector = [[FBRetainCycleDetector alloc] initWithConfiguration:configuration];
  
  [detector addCandidate:testObject];

  NSSet *retainCycles = [detector findRetainCycles];

  XCTAssertEqual([retainCycles count], 0);
}

- (void)testIfApplyingFilterToOnePropertyButSettingBothPropertiesWillStillYieldProperCycle
{
  FBGraphEdgeFilterTestClass *testObject = [FBGraphEdgeFilterTestClass new];
  testObject.filtered = testObject;
  testObject.filtered2 = testObject;

  NSArray *filterBlocks = @[FBFilterBlockWithObjectIvarRelation([FBGraphEdgeFilterTestClass class],
                                                                @"_filtered")];
  FBObjectGraphConfiguration *configuration =
  [[FBObjectGraphConfiguration alloc] initWithFilterBlocks:filterBlocks
                                       shouldInspectTimers:YES];

  FBRetainCycleDetector *detector = [[FBRetainCycleDetector alloc] initWithConfiguration:configuration];
  
  [detector addCandidate:testObject];

  NSSet *retainCycles = [detector findRetainCycles];
  NSSet *expectedCycles = [NSSet setWithObject:@[[[FBObjectiveCObject alloc] initWithObject:testObject]]];

  XCTAssertEqualObjects(retainCycles, expectedCycles);
}

- (void)testIfApplyingFilterForBothPropertiesWillFilterOutBothProperties
{
  FBGraphEdgeFilterTestClass *testObject = [FBGraphEdgeFilterTestClass new];
  testObject.filtered = testObject;
  testObject.filtered2 = testObject;

  NSArray *filterBlocks =
  @[FBFilterBlockWithObjectToManyIvarsRelation([FBGraphEdgeFilterTestClass class],
                                               [NSSet setWithArray:@[@"_filtered", @"_filtered2"]])];
  
  FBObjectGraphConfiguration *configuration =
  [[FBObjectGraphConfiguration alloc] initWithFilterBlocks:filterBlocks
                                       shouldInspectTimers:YES];

  FBRetainCycleDetector *detector = [[FBRetainCycleDetector alloc] initWithConfiguration:configuration];

  [detector addCandidate:testObject];

  NSSet *retainCycles = [detector findRetainCycles];

  XCTAssertEqual([retainCycles count], 0);
}

#endif //_INTERNAL_RCD_ENABLED

@end
