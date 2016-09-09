/**
 * Copyright (c) 2016-present, Facebook, Inc.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree. An additional grant
 * of patent rights can be found in the PATENTS file in the same directory.
 */

#import <objc/runtime.h>

#import <Foundation/Foundation.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 Returns object on given index for obj in its ivar layout.
 It will try to map the object to an Objective-C object, so if the index
 is invalid it will crash with BAD_ACCESS.

 It cannot be called under ARC.
 */
id FBExtractObjectByOffset(id obj, NSUInteger index);

#ifdef __cplusplus
}
#endif
