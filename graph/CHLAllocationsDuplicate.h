// Copyright 2004-present Facebook. All Rights Reserved.

#import <Foundation/Foundation.h>

#import <FBBaseLite/FBBaseDefines.h>
#import <malloc/malloc.h>

#ifdef __cplusplus
extern "C" {
#endif

  NS_ASSUME_NONNULL_BEGIN

  /**
   * Enumerates all live memory allocations by calling `block` for each allocation. Allocations are represented as a
   * `vm_range_t`.
   *
   * The memory ranges provided to the callback will be memory that contains a number of different kinds of data. Some
   * examples are: Objective-C objects, instances of Swift classes, C++ data created with the `new` operator, and of
   * course memory created with `malloc`.
   */
  void duplicateCHLEnumerateAllocationsWithBlock(void (^block)(vm_range_t range));

  NS_ASSUME_NONNULL_END

#ifdef __cplusplus
}
#endif
