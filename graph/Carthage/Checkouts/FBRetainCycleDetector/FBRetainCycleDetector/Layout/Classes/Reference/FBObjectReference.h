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
 Defines an outgoing reference from Objective-C object.
 */

@protocol FBObjectReference <NSObject>

/**
 What is the index of that reference in ivar layout?
 index * sizeof(void *) gives you offset from the
 beginning of the object.
 */
- (NSUInteger)indexInIvarLayout;

/**
 For given object we need to be able to grab that object reference.
 */
- (nullable id)objectReferenceFromObject:(nullable id)object;


/**
 For given reference in an object, there can be a path of names that leads to it.
 For example it can be an ivar, thus the path will consist of ivar name only:
 @[@"_myIvar"]

 But it also can be a reference in some nested struct like:
 struct SomeStruct {
   NSObject *myObject;
 };

 If that struct will be used in class, then name path would look like this:
 @[@"_myIvar", @"SomeStruct", @"myObject"]
 */
- (nullable NSArray<NSString *> *)namePath;

@end
