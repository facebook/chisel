//
//  CHLDuplicateDetection.m
//  Chisel
//
//  Copyright © 2016 Facebook. All rights reserved.
//

#if __has_feature(objc_arc)
#error CHLObjectDuplicateDetection.m expects ARC to be disabled.
#endif

#import "CHLDuplicateDetection.h"

#import "CHLObjectAllocations.h"

#import <objc/runtime.h>

NSArray *CHLFindDuplicates(Class cls, BOOL (^equalFunction)(id left, id right)) {
  NSMutableArray *objects = [NSMutableArray new];
  
  CHLEnumerateObjectsWithBlock(^(id object) {
    if ([object isKindOfClass:cls]) {
      [objects addObject:object];
    }
  });
 
  // Hold addresses only (so we won't call isEqual:)
  NSMutableSet *objectSet = [NSMutableSet new];
  NSUInteger objectsCount = objects.count;
  
  // O(n^2), we could probably base it on CFSet with custom callbacks to make it faster.
  for (NSUInteger i = 0; i < objectsCount; ++i) {
    for (NSUInteger j = i + 1; j < objectsCount; ++j) {
      if (equalFunction(objects[i], objects[j])) {
        [objectSet addObject:@((size_t)objects[i])];
        [objectSet addObject:@((size_t)objects[j])];
      }
    }
  }
  [objects release];
  
  NSMutableArray *duplicates = [NSMutableArray new];
  for (NSNumber *address in objectSet) {
    [duplicates addObject:(id)address.pointerValue];
  }
  [objectSet release];
  
  return [duplicates autorelease];
}
