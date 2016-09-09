/**
 * Copyright (c) 2016-present, Facebook, Inc.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree. An additional grant
 * of patent rights can be found in the PATENTS file in the same directory.
 */

#import <XCTest/XCTest.h>

#import <FBRetainCycleDetector/FBObjectiveCBlock.h>
#import <FBRetainCycleDetector/FBObjectiveCGraphElement+Internal.h>
#import <FBRetainCycleDetector/FBObjectiveCObject.h>

#import <FBRetaincycleDetector/FBRetainCycleDetector.h>

typedef void (^_RCDTestBlockType)();

@interface FBObjectiveCBlockTests : XCTestCase
@end

@implementation FBObjectiveCBlockTests

#if _INTERNAL_RCD_ENABLED

- (void)testLayoutForBlockRetainingObjectWillFetchTheObject
{
  NSObject *someObject = [NSObject new];
  __block NSObject *unretainedObject;

  _RCDTestBlockType block = ^{
    // Keep strong reference to someObject
    unretainedObject = someObject;
  };

  FBObjectiveCObject *wrappedObject = [[FBObjectiveCObject alloc] initWithObject:someObject];
  FBObjectiveCBlock *wrappedBlock = [[FBObjectiveCBlock alloc] initWithObject:block];

  NSSet *retainedObjects = [wrappedBlock allRetainedObjects];
  XCTAssertTrue([retainedObjects containsObject:wrappedObject]);
}

- (void)testLayoutForBlockRetainingOtherBlockWillFetchTheBlock
{
  _RCDTestBlockType block1 = ^{};
  _RCDTestBlockType block2 = ^{
    block1();
  };

  FBObjectiveCBlock *wrappedBlock1 = [[FBObjectiveCBlock alloc] initWithObject:block1];
  FBObjectiveCBlock *wrappedBlock2 = [[FBObjectiveCBlock alloc] initWithObject:block2];

  NSSet *retainedObjects = [wrappedBlock2 allRetainedObjects];
  XCTAssertTrue([retainedObjects containsObject:wrappedBlock1]);
}

- (void)testLayoutForBlockRetainingFewObjectsWillFetchAllOfThem
{
  NSObject *someObject1 = [NSObject new];
  NSObject *someObject2 = [NSObject new];
  NSObject *someObject3 = [NSObject new];
  __block NSObject *unretainedObject;

  _RCDTestBlockType block = ^{
    // Keep strong reference to someObject
    unretainedObject = someObject1;
    unretainedObject = someObject2;
    unretainedObject = someObject3;
  };

  FBObjectiveCObject *wrappedObject1 = [[FBObjectiveCObject alloc] initWithObject:someObject1];
  FBObjectiveCObject *wrappedObject2 = [[FBObjectiveCObject alloc] initWithObject:someObject2];
  FBObjectiveCObject *wrappedObject3 = [[FBObjectiveCObject alloc] initWithObject:someObject3];
  FBObjectiveCBlock *wrappedBlock = [[FBObjectiveCBlock alloc] initWithObject:block];

  NSSet *retainedObjects = [wrappedBlock allRetainedObjects];

  XCTAssertTrue([retainedObjects containsObject:wrappedObject1]);
  XCTAssertTrue([retainedObjects containsObject:wrappedObject2]);
  XCTAssertTrue([retainedObjects containsObject:wrappedObject3]);
}

- (void)testLayoutForBlockKeepingObjectBlockMixin
{
  NSObject *someObject1 = [NSObject new];
  NSObject *someObject2 = [NSObject new];
  NSObject *someObject3 = [NSObject new];
  _RCDTestBlockType someBlock1 = ^{};
  _RCDTestBlockType someBlock2 = ^{};
  _RCDTestBlockType someBlock3 = ^{};
  __block NSObject *unretainedObject;

  _RCDTestBlockType block = ^{
    // Keep strong reference to someObject
    someBlock1();
    unretainedObject = someObject1;
    unretainedObject = someObject2;
    someBlock2();
    someBlock3();
    unretainedObject = someObject3;
  };

  FBObjectiveCObject *wrappedObject1 = [[FBObjectiveCObject alloc] initWithObject:someObject1];
  FBObjectiveCObject *wrappedObject2 = [[FBObjectiveCObject alloc] initWithObject:someObject2];
  FBObjectiveCObject *wrappedObject3 = [[FBObjectiveCObject alloc] initWithObject:someObject3];
  FBObjectiveCBlock *wrappedBlock1 = [[FBObjectiveCBlock alloc] initWithObject:someBlock1];
  FBObjectiveCBlock *wrappedBlock2 = [[FBObjectiveCBlock alloc] initWithObject:someBlock2];
  FBObjectiveCBlock *wrappedBlock3 = [[FBObjectiveCBlock alloc] initWithObject:someBlock3];
  FBObjectiveCBlock *wrappedBlock = [[FBObjectiveCBlock alloc] initWithObject:block];

  NSSet *retainedObjects = [wrappedBlock allRetainedObjects];
  XCTAssertTrue([retainedObjects containsObject:wrappedObject1]);
  XCTAssertTrue([retainedObjects containsObject:wrappedObject2]);
  XCTAssertTrue([retainedObjects containsObject:wrappedObject3]);
  XCTAssertTrue([retainedObjects containsObject:wrappedBlock1]);
  XCTAssertTrue([retainedObjects containsObject:wrappedBlock2]);
  XCTAssertTrue([retainedObjects containsObject:wrappedBlock3]);
}

- (void)testLayoutForEmptyBlockWillBeEmpty
{
  _RCDTestBlockType block = ^{};
  FBObjectiveCBlock *wrappedBlock = [[FBObjectiveCBlock alloc] initWithObject:block];
  NSSet *retainedObjects = [wrappedBlock allRetainedObjects];
  XCTAssertEqual([retainedObjects count], 0);
}

#endif //_INTERNAL_RCD_ENABLED

@end
