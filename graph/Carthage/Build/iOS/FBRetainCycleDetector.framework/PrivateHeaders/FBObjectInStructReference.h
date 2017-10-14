/**
 * Copyright (c) 2016-present, Facebook, Inc.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree. An additional grant
 * of patent rights can be found in the PATENTS file in the same directory.
 */

#import <Foundation/Foundation.h>

#import "FBObjectReference.h"

/**
 Struct object is an Objective-C object that is created inside
 a struct. In Objective-C++ that object will be retained
 by an object owning the struct, therefore will be listed in
 ivar layout for the class.
 */

@interface FBObjectInStructReference : NSObject <FBObjectReference>

- (nonnull instancetype)initWithIndex:(NSUInteger)index
                             namePath:(nullable NSArray<NSString *> *)namePath;

@end
