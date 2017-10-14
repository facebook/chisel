/**
 * Copyright (c) 2016-present, Facebook, Inc.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree. An additional grant
 * of patent rights can be found in the PATENTS file in the same directory.
 */

#import <memory>
#import <unordered_map>
#import <vector>

#import <XCTest/XCTest.h>

#import <FBRetainCycleDetector/FBBlockStrongLayout.h>
#import <FBRetainCycleDetector/FBRetainCycleUtils.h>
@interface FBBlockStrongLayoutTests : XCTestCase
@end

@implementation FBBlockStrongLayoutTests

- (void)testBlockDoesntRetainWeakReference
{
  __attribute__((objc_precise_lifetime)) NSObject *object = [NSObject new];
  __weak NSObject *weakObject = object;
  
  void (^block)() = ^{
    __unused NSObject *someObject = weakObject;
  };
  
  NSArray *retainedObjects = FBGetBlockStrongReferences((__bridge void *)(block));
  
  XCTAssertEqual([retainedObjects count], 0);
}

- (void)testBlockRetainsStrongReference
{
  NSObject *object = [NSObject new];
  
  void (^block)() = ^{
    __unused NSObject *someObject = object;
  };
  
  NSArray *retainedObjects = FBGetBlockStrongReferences((__bridge void *)(block));
  
  XCTAssertEqual([retainedObjects count], 1);
  XCTAssertEqualObjects(retainedObjects[0], object);
}

- (void)testThatBlockRetainingVectorOfObjectsDoNotCrash
{
  NSObject *object = [NSObject new];
  std::vector<id> vector = {object};
  
  void (^block)() = ^{
    __unused std::vector<id> someVector = vector;
  };
  
  NSArray *retainedObjects = FBGetBlockStrongReferences((__bridge void *)(block));
  
  XCTAssertEqual([retainedObjects count], 0);
}

- (void)testThatBlockRetainingVectorOfStructsDoNotCrash
{
  struct HelperStruct {};
  std::vector<HelperStruct> vector = {};
  
  void (^block)() = ^{
    __unused std::vector<HelperStruct> someVector = vector;
  };
  
  NSArray *retainedObjects = FBGetBlockStrongReferences((__bridge void *)(block));
  
  XCTAssertEqual([retainedObjects count], 0);
}

- (void)testThatBlockUsingCppButRetainingOnlyObjectsWillReturnTheObjectAndNotCrash
{
  NSObject *object = [NSObject new];
  
  void (^block)() = ^{
    std::vector<id> vector;
    vector.push_back(object);
  };
  
  NSArray *retainedObjects = FBGetBlockStrongReferences((__bridge void *)(block));
  
  XCTAssertEqual([retainedObjects count], 1);
  XCTAssertEqualObjects(retainedObjects[0], object);
}

- (void)testThatBlockRetainingMapWillNotCrash
{
  struct HelperStruct{};
  std::unordered_map<int, HelperStruct> map;
  
  void (^block)() = ^{
    __unused std::unordered_map<int, HelperStruct> someMap = map;
  };
  
  NSArray *retainedObjects = FBGetBlockStrongReferences((__bridge void *)(block));
  
  XCTAssertEqual([retainedObjects count], 0);
}

@end
