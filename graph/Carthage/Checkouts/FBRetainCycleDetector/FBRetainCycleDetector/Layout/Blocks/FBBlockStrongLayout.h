/**
 * Copyright (c) 2016-present, Facebook, Inc.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree. An additional grant
 * of patent rights can be found in the PATENTS file in the same directory.
 */

#import <Foundation/Foundation.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 Returns an array of id<FBObjectReference> objects that will have only those references
 that are retained by block.
 */
NSArray *_Nullable FBGetBlockStrongReferences(void *_Nonnull block);

BOOL FBObjectIsBlock(void *_Nullable object);
  
#ifdef __cplusplus
}
#endif
