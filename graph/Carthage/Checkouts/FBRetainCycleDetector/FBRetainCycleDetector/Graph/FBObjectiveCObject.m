/**
 * Copyright (c) 2016-present, Facebook, Inc.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree. An additional grant
 * of patent rights can be found in the PATENTS file in the same directory.
 */

#import "FBObjectiveCObject.h"

#import <objc/runtime.h>

#import "FBClassStrongLayout.h"
#import "FBObjectGraphConfiguration.h"
#import "FBObjectReference.h"
#import "FBRetainCycleUtils.h"

@implementation FBObjectiveCObject

- (NSSet *)allRetainedObjects
{
  Class aCls = object_getClass(self.object);
  if (!self.object || !aCls) {
    return nil;
  }

  NSArray *strongIvars = FBGetObjectStrongReferences(self.object, self.configuration.layoutCache);

  NSMutableArray *retainedObjects = [[[super allRetainedObjects] allObjects] mutableCopy];

  for (id<FBObjectReference> ref in strongIvars) {
    id referencedObject = [ref objectReferenceFromObject:self.object];

    if (referencedObject) {
      NSArray<NSString *> *namePath = [ref namePath];
      FBObjectiveCGraphElement *element = FBWrapObjectGraphElementWithContext(self,
                                                                              referencedObject,
                                                                              self.configuration,
                                                                              namePath);
      if (element) {
        [retainedObjects addObject:element];
      }
    }
  }

  if ([NSStringFromClass(aCls) hasPrefix:@"__NSCF"]) {
    /**
     If we are dealing with toll-free bridged collections, we are not guaranteed that the collection
     will hold only Objective-C objects. We are not able to check in runtime what callbacks it uses to
     retain/release (if any) and we could easily crash here.
     */
    return [NSSet setWithArray:retainedObjects];
  }

  if (class_isMetaClass(aCls)) {
    // If it's a meta-class it can conform to following protocols,
    // but it would crash when trying enumerating
    return nil;
  }

  if ([aCls conformsToProtocol:@protocol(NSFastEnumeration)]) {
    BOOL retainsKeys = [self _objectRetainsEnumerableKeys];
    BOOL retainsValues = [self _objectRetainsEnumerableValues];

    BOOL isKeyValued = NO;
    if ([aCls instancesRespondToSelector:@selector(objectForKey:)]) {
      isKeyValued = YES;
    }

    /**
     This codepath is prone to errors. When you enumerate a collection that can be mutated while enumeration
     we fall into risk of crash. To save ourselves from that we will catch such exception and try again.
     We should not try this endlessly, so at some point we will simply give up.
     */
    NSInteger tries = 10;
    for (NSInteger i = 0; i < tries; ++i) {
      // If collection is mutated we want to rollback and try again - let's keep refs in temporary set
      NSMutableSet *temporaryRetainedObjects = [NSMutableSet new];
      @try {
        for (id subobject in self.object) {
          if (retainsKeys) {
            FBObjectiveCGraphElement *element = FBWrapObjectGraphElement(self, subobject, self.configuration);
            if (element) {
              [temporaryRetainedObjects addObject:element];
            }
          }
          if (isKeyValued && retainsValues) {
            FBObjectiveCGraphElement *element = FBWrapObjectGraphElement(self,
                                                                         [self.object objectForKey:subobject],
                                                                         self.configuration);
            if (element) {
              [temporaryRetainedObjects addObject:element];
            }
          }
        }
      }
      @catch (NSException *exception) {
        // mutation happened, we want to try enumerating again
        continue;
      }

      // If we are here it means no exception happened and we want to break outer loop
      [retainedObjects addObjectsFromArray:[temporaryRetainedObjects allObjects]];
      break;
    }
  }

  return [NSSet setWithArray:retainedObjects];
}

- (BOOL)_objectRetainsEnumerableValues
{
  if ([self.object respondsToSelector:@selector(valuePointerFunctions)]) {
    NSPointerFunctions *pointerFunctions = [self.object valuePointerFunctions];
    if (pointerFunctions.usesWeakReadAndWriteBarriers) {
      return NO;
    }
  }

  return YES;
}

- (BOOL)_objectRetainsEnumerableKeys
{
  if ([self.object respondsToSelector:@selector(pointerFunctions)]) {
    // NSHashTable and similar
    // If object shows what pointer functions are used, lets try to determine
    // if it's not retaining objects
    NSPointerFunctions *pointerFunctions = [self.object pointerFunctions];
    if (pointerFunctions.usesWeakReadAndWriteBarriers) {
      // It's weak - we should not touch it
      return NO;
    }
  }

  if ([self.object respondsToSelector:@selector(keyPointerFunctions)]) {
    NSPointerFunctions *pointerFunctions = [self.object keyPointerFunctions];
    if (pointerFunctions.usesWeakReadAndWriteBarriers) {
      return NO;
    }
  }

  return YES;
}

@end
