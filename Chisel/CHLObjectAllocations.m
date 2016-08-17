//
//  CHLObjectAllocations.m
//  Chisel
//
//  Copyright © 2016 Facebook. All rights reserved.
//

#if __has_feature(objc_arc)
#error CHLObjectAllocations.m expects ARC to be disabled.
#endif

#import "CHLAllocations.h"

#import <objc/runtime.h>

void CHLEnumerateObjectsWithBlock(void (^block)(id object))
{
  unsigned int classCount;
  Class *classList = objc_copyClassList(&classCount);
  NSPointerFunctionsOptions options = NSPointerFunctionsOpaqueMemory|NSPointerFunctionsOpaquePersonality;
  NSHashTable *classes = [[NSHashTable alloc] initWithOptions:options capacity:classCount];
  for (unsigned int i = 0; i < classCount; i++) {
    [classes addObject:classList[i]];
  }
  free(classList);
  
  CHLEnumerateAllocationsWithBlock(^(vm_range_t range) {
    if (range.size < sizeof(struct objc_object)) {
      return;
    }
    
    id object = (id)range.address;
    Class class_ = object_getClass(object);
    
    if (![classes containsObject:class_]) {
      return;
    }
    
    if (range.size < class_getInstanceSize(class_)) {
      return;
    }
    
    if (range.size > class_getInstanceSize(class_) && object_getIndexedIvars(object) == NULL) {
      return;
    }
    
    block(object);
  });
}
