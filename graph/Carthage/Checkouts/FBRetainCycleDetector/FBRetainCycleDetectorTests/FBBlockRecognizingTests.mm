/**
 * Copyright (c) 2016-present, Facebook, Inc.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree. An additional grant
 * of patent rights can be found in the PATENTS file in the same directory.
 */

#if __has_feature(objc_arc)
#error This file must be compiled with MRR. Use -fno-objc-arc flag.
#endif

#import <XCTest/XCTest.h>

#import <FBRetainCycleDetector/FBBlockStrongLayout.h>
#import <FBRetainCycleDetector/FBRetainCycleDetector.h>

@interface FBBlockRecognizingTests : XCTestCase
@end

void (^_RCDTestGlobalBlock)(void) = ^{};

@implementation FBBlockRecognizingTests

- (void)testThatGlobalBlockWillBeRecognizedAsBlock
{
  XCTAssertTrue(FBObjectIsBlock(_RCDTestGlobalBlock));
}

- (void)testThatHeapBlockWillBeRecognizedAsBlock
{
  int i = 0;
  void (^_RCDTestHeapBlock)(void) = ^{
    printf("%d", i);
  };

  XCTAssertTrue(FBObjectIsBlock([[_RCDTestHeapBlock copy] autorelease]));
}

- (void)testThatStackBlockWillBeRecognizedAsBlock
{
  int i = 0;

  void (^testStackBlock)(void) = ^{
    printf("%d", i);
  };

  XCTAssertTrue(FBObjectIsBlock(testStackBlock));
}

@end
