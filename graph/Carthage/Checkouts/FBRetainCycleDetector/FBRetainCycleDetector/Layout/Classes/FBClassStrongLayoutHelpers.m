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

#import "FBClassStrongLayoutHelpers.h"

id FBExtractObjectByOffset(id obj, NSUInteger index) {
  id *idx = (id *)((uintptr_t)obj + (index * sizeof(void *)));

  return *idx;
}
