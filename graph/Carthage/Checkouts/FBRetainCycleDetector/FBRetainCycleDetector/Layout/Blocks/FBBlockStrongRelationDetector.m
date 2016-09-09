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

#import "FBBlockStrongRelationDetector.h"

#import <objc/runtime.h>

static void byref_keep_nop(struct _block_byref_block *dst, struct _block_byref_block *src) {}
static void byref_dispose_nop(struct _block_byref_block *param) {}

@implementation FBBlockStrongRelationDetector

- (oneway void)release
{
  _strong = YES;
}

- (id)retain
{
  return self;
}

+ (id)alloc
{
  FBBlockStrongRelationDetector *obj = [super alloc];

  // Setting up block fakery
  obj->forwarding = obj;
  obj->byref_keep = byref_keep_nop;
  obj->byref_dispose = byref_dispose_nop;

  return obj;
}

- (oneway void)trueRelease
{
  [super release];
}

@end
