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
#include <unordered_set>

#include <objc/objc.h>
#include <objc/runtime.h>

@interface _CHLObjCAllocChecker : NSObject
- (BOOL)isStandardAllocUsedByClass:(Class)cls;
@end

@implementation CHLObjCObjectRecognizer
{
  std::unordered_set<Class> _classSet;
  _CHLObjCAllocChecker *_allocChecker;
}

- (instancetype)init
{
  self = [super init];
  if (self != nil) {
    _allocChecker = [_CHLObjCAllocChecker new];

    unsigned int count;
    const auto classList = objc_copyClassList(&count);
    for (unsigned int i = 0; i < count; ++i) {
      _classSet.insert(classList[i]);
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
  if (_classSet.find(cls) == _classSet.cend()) {
    return NO;
  }

  // The memory size must be at least the instance size of the class, rounded up to the nearest allocator size.
  const auto goodInstanceSize = malloc_good_size(class_getInstanceSize(cls));
  if (range.size < goodInstanceSize) {
    return NO;
  }

  // The memory size must either equal the instance size, or can be bigger if the class overrides +alloc.
  if (range.size > goodInstanceSize && [_allocChecker isStandardAllocUsedByClass:cls]) {
    return NO;
  }

  // TODO (maybe): Check that the ivars of object type ('@') point to valid objects, or are nil.

  return YES;
}

@end

@implementation _CHLObjCAllocChecker
{
  IMP _objectAllocWithZone;
  IMP _objectAlloc;
  std::unordered_map<Class, bool> _cache;
}

- (instancetype)init
{
  self = [super init];
  if (self != nil) {
    const Class objectMetaClass = objc_getMetaClass("NSObject");
    _objectAllocWithZone = class_getMethodImplementation(objectMetaClass, @selector(allocWithZone:));
    _objectAlloc = class_getMethodImplementation(objectMetaClass, @selector(alloc));
  }
  return self;
}

- (BOOL)isStandardAllocUsedByClass:(Class)cls
{
  const auto match = _cache.find(cls);
  if (match != _cache.cend()) {
    return match->second;
  }

  const Class metaClass = object_getClass(cls);
  const bool usesStandardAlloc =
    class_getMethodImplementation(metaClass, @selector(allocWithZone:)) == _objectAllocWithZone &&
    class_getMethodImplementation(metaClass, @selector(alloc)) == _objectAlloc;

  return _cache[cls] = usesStandardAlloc;
}

@end
