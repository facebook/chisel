/**
 * Copyright (c) 2016-present, Facebook, Inc.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree. An additional grant
 * of patent rights can be found in the PATENTS file in the same directory.
 */

#import "FBNodeEnumerator.h"

#import "FBObjectiveCGraphElement.h"

@implementation FBNodeEnumerator
{
  NSSet *_retainedObjectsSnapshot;
  NSEnumerator *_enumerator;
}

- (instancetype)initWithObject:(FBObjectiveCGraphElement *)object
{
  if (self = [super init]) {
    _object = object;
  }

  return self;
}

- (FBNodeEnumerator *)nextObject
{
  if (!_object) {
    return nil;
  } else if (!_retainedObjectsSnapshot) {
    _retainedObjectsSnapshot = [_object allRetainedObjects];
    _enumerator = [_retainedObjectsSnapshot objectEnumerator];
  }

  FBObjectiveCGraphElement *next = [_enumerator nextObject];

  if (next) {
    return [[FBNodeEnumerator alloc] initWithObject:next];
  }

  return nil;
}

- (BOOL)isEqual:(id)object
{
  if ([object isKindOfClass:[FBNodeEnumerator class]]) {
    FBNodeEnumerator *enumerator = (FBNodeEnumerator *)object;
    return [self.object isEqual:enumerator.object];
  }

  return NO;
}

- (NSUInteger)hash
{
  return [self.object hash];
}

@end
