//
//  ChiselTests.m
//  ChiselTests
//
//  Copyright © 2016 Facebook. All rights reserved.
//

#import <XCTest/XCTest.h>

#import "CHLAllocations.h"

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

- (void)testAllocationsIncludesFreshMalloc
{
  u_int32_t size = MAX(arc4random_uniform(UINT8_MAX), 1);
  void *memory = malloc(size);

  __block BOOL seenMalloc = NO;
  CHLEnumerateAllocationsWithBlock(^(vm_range_t range) {
    if (range.address == (vm_address_t)memory) {
      XCTAssertGreaterThanOrEqual(range.size, size);
      seenMalloc = YES;
    }
  });

  free(memory);

  XCTAssertTrue(seenMalloc);
}

@end
