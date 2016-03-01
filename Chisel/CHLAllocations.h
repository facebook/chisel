//
//  CHLAllocations.h
//  Chisel
//
//  Copyright © 2016 Facebook. All rights reserved.
//

#import <Foundation/Foundation.h>

#import <malloc/malloc.h>

NS_ASSUME_NONNULL_BEGIN

/**
 * Enumerates all live memory allocations by calling `block` for each allocation. Allocations are represented as a
 * `vm_range_t`.
 *
 * The memory ranges provided to the callback will be memory that contains a number of different kinds of data. Some
 * examples are: Objective-C objects, instances of Swift classes, C++ data created with the `new` operator, and of
 * course memory created with `malloc`.
 */
void CHLEnumerateAllocationsWithBlock(void (^block)(vm_range_t range));

NS_ASSUME_NONNULL_END
