//
//  ChiselTests.m
//  ChiselTests
//
//  Copyright © 2016 Facebook. All rights reserved.
//

#import <XCTest/XCTest.h>

#import "CHLFunctions.h"

@interface ChiselTests : XCTestCase
@end

@implementation ChiselTests

- (void)testAllocationsIncludesSelf
{
  __block BOOL seenSelf = NO;
  CHLEnumerateAllocationsWithBlock(^(vm_range_t range) {
    if (range.address == (vm_address_t)self) {
      seenSelf = YES;
    }
  });

  XCTAssertTrue(seenSelf);
}

@end
