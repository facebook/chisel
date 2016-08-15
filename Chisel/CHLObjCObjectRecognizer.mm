//
//  CHLObjCObjectRecognizer.m
//  Chisel
//
//  Copyright © 2016 Facebook. All rights reserved.
//

#if __has_feature(objc_arc)
#error CHLObjCObjectRecognizer.m expects ARC to be disabled.
#endif

#import "CHLObjCObjectRecognizer.h"

#include <unordered_map>

#include <objc/objc.h>
#include <objc/runtime.h>

@implementation CHLObjCObjectRecognizer
{
  // This is primarily used for set lookup of classes, hence the name,
  // but also records whether a class overrides +alloc/+allocWithZone:
  std::unordered_map<Class, bool> _classSet;
}

static bool overridesAlloc(Class cls)
{
  static IMP objectAllocWithZone = NULL;
  static IMP objectAlloc = NULL;
  if (objectAllocWithZone == NULL || objectAlloc == NULL) {
    const Class objectMetaClass = objc_getMetaClass("NSObject");
    objectAllocWithZone = class_getMethodImplementation(objectMetaClass, @selector(allocWithZone:));
    objectAlloc = class_getMethodImplementation(objectMetaClass, @selector(alloc));
  }

  const Class metaClass = object_getClass(cls);
  return
    class_getMethodImplementation(metaClass, @selector(allocWithZone:)) != objectAllocWithZone ||
    class_getMethodImplementation(metaClass, @selector(alloc)) != objectAlloc;
}

- (instancetype)init
{
  self = [super init];
  if (self != nil) {
    unsigned int count;
    const auto classList = objc_copyClassList(&count);
    for (unsigned int i = 0; i < count; ++i) {
      const auto cls = classList[i];
      _classSet.emplace(cls, overridesAlloc(cls));
    }
    free(classList);
  }
  return self;
}

- (BOOL)appearsToRecognize:(vm_range_t)range
{
  assert(range.size >= sizeof(objc_object));

  const id object = reinterpret_cast<id>(range.address);
  const auto cls = object_getClass(object);

  // The class/isa must be in the set of classes known by the runtime.
  const auto entry = _classSet.find(cls);
  if (entry == _classSet.cend()) {
    return NO;
  }

  // The memory size must be at least the instance size of the class, rounded up to the nearest allocator size.
  const auto goodInstanceSize = malloc_good_size(class_getInstanceSize(cls));
  if (range.size < goodInstanceSize) {
    return NO;
  }

  // The memory size must either equal the instance size, or can be bigger if the class overrides +alloc.
  const bool overridesAlloc = entry->second;
  if (range.size > goodInstanceSize && !overridesAlloc) {
    return NO;
  }

  // TODO (maybe): Check that the ivars of object type ('@') point to valid objects, or are nil.

  return YES;
}

@end
