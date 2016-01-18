//
//  CHLAllocations.h
//  Chisel
//
//  Copyright © 2016 Facebook. All rights reserved.
//

#import <Foundation/Foundation.h>

#import <malloc/malloc.h>

/**
 * Enumerates all live memory allocations by calling `block` for each malloc range (represented as a `vm_range_t`).
 */
void CHLEnumerateAllocationsWithBlock(void (^block)(vm_range_t range));
