/**
 * Copyright (c) 2016-present, Facebook, Inc.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree. An additional grant
 * of patent rights can be found in the PATENTS file in the same directory.
 */

#import <Foundation/Foundation.h>

/**
 We created a detector object that will fake *any* object that block can retain.

 Using clever trickery from Circle:
 https://github.com/mikeash/Circle/blob/master/Circle/CircleIVarLayout.m

 We are also faking that this object can be treated as a block.
 Otherwise if the block is retained by block, it will try to call byref_dispose and
 our object won't be able to respond.
 */

struct _block_byref_block;
@interface FBBlockStrongRelationDetector : NSObject
{
  // __block fakery
  void *forwarding;
  int flags;   //refcount;
  int size;
  void (*byref_keep)(struct _block_byref_block *dst, struct _block_byref_block *src);
  void (*byref_dispose)(struct _block_byref_block *);
  void *captured[16];
}

@property (nonatomic, assign, getter=isStrong) BOOL strong;

- (oneway void)trueRelease;

@end
