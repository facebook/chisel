/**
 * Copyright (c) 2016-present, Facebook, Inc.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree. An additional grant
 * of patent rights can be found in the PATENTS file in the same directory.
 */

#import "FBObjectiveCGraphElement+Internal.h"

#import <objc/message.h>
#import <objc/runtime.h>

#import "FBAssociationManager.h"
#import "FBClassStrongLayout.h"
#import "FBObjectGraphConfiguration.h"
#import "FBRetainCycleUtils.h"
#import "FBRetainCycleDetector.h"

@implementation FBObjectiveCGraphElement

- (instancetype)initWithObject:(id)object
{
  return [self initWithObject:object
                configuration:[FBObjectGraphConfiguration new]];
}

- (instancetype)initWithObject:(id)object
                 configuration:(nonnull FBObjectGraphConfiguration *)configuration
{
  return [self initWithObject:object
                configuration:configuration
                     namePath:nil];
}

- (instancetype)initWithObject:(id)object
                 configuration:(nonnull FBObjectGraphConfiguration *)configuration
                      namePath:(NSArray<NSString *> *)namePath
{
  if (self = [super init]) {
#if _INTERNAL_RCD_ENABLED
    // We are trying to mimic how ObjectiveC does storeWeak to not fall into
    // _objc_fatal path
    // https://github.com/bavarious/objc4/blob/3f282b8dbc0d1e501f97e4ed547a4a99cb3ac10b/runtime/objc-weak.mm#L369

    Class aCls = object_getClass(object);

    BOOL (*allowsWeakReference)(id, SEL) =
    (__typeof__(allowsWeakReference))class_getMethodImplementation(aCls, @selector(allowsWeakReference));

    if (allowsWeakReference && (IMP)allowsWeakReference != _objc_msgForward) {
      if (allowsWeakReference(object, @selector(allowsWeakReference))) {
        // This is still racey since allowsWeakReference could change it value by now.
        _object = object;
      }
    } else {
      _object = object;
    }
#endif
    _namePath = namePath;
    _configuration = configuration;
  }

  return self;
}

- (NSSet *)allRetainedObjects
{
  NSArray *retainedObjectsNotWrapped = [FBAssociationManager associationsForObject:_object];
  NSMutableSet *retainedObjects = [NSMutableSet new];

  for (id obj in retainedObjectsNotWrapped) {
    FBObjectiveCGraphElement *element = FBWrapObjectGraphElementWithContext(self,
                                                                            obj,
                                                                            _configuration,
                                                                            @[@"__associated_object"]);
    if (element) {
      [retainedObjects addObject:element];
    }
  }

  return retainedObjects;
}

- (BOOL)isEqual:(id)object
{
  if ([object isKindOfClass:[FBObjectiveCGraphElement class]]) {
    FBObjectiveCGraphElement *objcObject = object;
    // Use pointer equality
    return objcObject.object == _object;
  }
  return NO;
}

- (NSUInteger)hash
{
  return (size_t)_object;
}

- (NSString *)description
{
  if (_namePath) {
    NSString *namePathStringified = [_namePath componentsJoinedByString:@" -> "];
    return [NSString stringWithFormat:@"-> %@ -> %@ ", namePathStringified, object_getClass(_object)];
  }
  return [NSString stringWithFormat:@"-> %@ ", object_getClass(_object)];
}

- (size_t)objectAddress
{
  return (size_t)_object;
}

- (NSString *)classNameOrNull
{
  NSString *className = NSStringFromClass(object_getClass(_object));
  if (!className) {
    className = @"Null";
  }

  return className;
}

- (Class)objectClass
{
  return object_getClass(_object);
}

@end
