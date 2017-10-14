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

#import "FBObjectReference.h"

typedef NS_ENUM(NSUInteger, FBType) {
  FBObjectType,
  FBBlockType,
  FBStructType,
  FBUnknownType,
};

@interface FBIvarReference : NSObject <FBObjectReference>

@property (nonatomic, copy, readonly, nullable) NSString *name;
@property (nonatomic, readonly) FBType type;
@property (nonatomic, readonly) ptrdiff_t offset;
@property (nonatomic, readonly) NSUInteger index;
@property (nonatomic, readonly, nonnull) Ivar ivar;

- (nonnull instancetype)initWithIvar:(nonnull Ivar)ivar;

@end
