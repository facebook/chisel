//
//  CHLObjectAllocations.h
//  Chisel
//
//  Copyright © 2016 Facebook. All rights reserved.
//

#ifndef CHLObjectAllocations_h
#define CHLObjectAllocations_h

/**
 * Enumerates all live objects by calling `block` for each object.
 */
void CHLEnumerateObjectsWithBlock(void (^block)(id object));

#endif /* CHLObjectAllocations_h */
