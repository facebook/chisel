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
 FBAssociationManager is a tracker of object associations. For given object it can return all objects that
 are being retained by this object with objc_setAssociatedObject & retain policy.
 */
@interface FBAssociationManager : NSObject

/**
 Start tracking associations. It will use fishhook to swizzle C methods:
 objc_(set/remove)AssociatedObject and inject some tracker code.
 */
+ (void)hook;

/**
 Stop tracking associations, fishhooks.
 */
+ (void)unhook;

/**
 For given object return all objects that are retained by it using associated objects.

 @return NSArray of objects associated with given object
 */
+ (nullable NSArray *)associationsForObject:(nullable id)object;

@end
