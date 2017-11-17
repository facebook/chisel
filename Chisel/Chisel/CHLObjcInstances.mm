// Copyright 2004-present Facebook. All Rights Reserved.

#import "CHLObjcInstances.h"

#import <Foundation/Foundation.h>

#include "CHLAllocations.h"

#include <dlfcn.h>
#include <objc/message.h>
#include <objc/runtime.h>
#include <mach-o/getsect.h>
#if !defined(__LP64__)
using mach_header_t = mach_header;
#else
using mach_header_t = mach_header_64;
#endif

#include <unordered_set>
#include <vector>

#if __has_feature(objc_arc)
#error Disable ARC for this file
#endif

// Informal protocol to make it easy to call -_isDeallocating
@interface NSObject (Private)
- (BOOL)_isDeallocating;
@end

static id embeddedObjcInstance(vm_range_t range) {
  Dl_info info;
  bool aligned = range.address % alignof(void *) == 0;
  uint8_t *pointer = (uint8_t *)range.address;
  if (aligned && dladdr(pointer, &info)) {
    unsigned long size = 0;
    uint8_t *start = getsectiondata((mach_header_t *)info.dli_fbase, SEG_DATA, "__cfstring", &size);
    uint8_t *end = start + size;
    if (start <= pointer || pointer < end) {
      // Found NSString/CFString constant.
      return reinterpret_cast<id>(range.address);
    }
  }
  return nil;
}

// TODO: Should this cache results instead of repeated lookups.
bool isFixedSizeClass(Class cls) {
  const auto meta = object_getClass(cls);
  const auto root = objc_getMetaClass("NSObject");

  SEL allocs[] = { @selector(allocWithZone:), @selector(alloc) };
  for (const auto &sel : allocs) {
    IMP imp = class_getMethodImplementation(meta, sel);
    if (imp != class_getMethodImplementation(root, sel)) {
      // Class overrides NSObject alloc method, may not have fixed sizes.
      return false;
    }
  }

  return true;
}

// Runs a number of heuristics on the given address. Returns nil if any heuristic fails, otherwise
// returns that address casted as an object.
//
// Currently the heuristics don't fully guarantee that the returned object is an actual object, but
// when using MallocScribble=1, false positives are unlikely. Further, callers will generally do
// higher level filtering, for example checking a value on the object, which can further eliminate
// false positives.
//
// There's also one known false negative case, NSConcreteValue can store data in the malloc memory
// beyond its instance size. Currently this false negative is allowed.
id CHLViableObjcInstance(vm_range_t range, const std::unordered_set<Class> &classSet)
{
  // Check if this address points to an object embedded into Mach-O.
  if (range.size == 0) {
    return embeddedObjcInstance(range);
  }

  id obj = reinterpret_cast<id>(range.address);

  // It's safe to call object_getClass on memory that isn't objc objects.
  // Check that the returned Class points to an expected class.
  Class cls = object_getClass(obj);
  if (classSet.find(cls) == classSet.end()) {
    return nil;
  }

  // Instance size is the byte count needed for an object's ivars, plus any padding.
  // Allocation size is the byte count that malloc will actually allocate for instances of a Class.
  const auto instanceSize = class_getInstanceSize(cls);
  const auto expectedAllocationSize = malloc_good_size(instanceSize);
  const auto extraSize = expectedAllocationSize - instanceSize;

  const bool debug = getenv("FINDINSTANCES_DEBUG") != NULL;

  if (range.size < expectedAllocationSize) {
    if (debug) {
      printf("%p has class %s but is too small\n", obj, class_getName(cls));
    }
    return nil;
  }

  if (range.size > expectedAllocationSize && isFixedSizeClass(cls)) {
    // Range is too big and the class has no way of allocating larger instances.
    if (debug) {
      printf("%p has fixed size class %s but is too large\n", obj, class_getName(cls));
    }
    return nil;
  }

  if (range.size == expectedAllocationSize && extraSize) {
    // ObjC instances are allocated with calloc, memory beyond the instance size should be zeros.
    // Some classes have been known to store data in the extra space, ex NSConcreteValue.
    static const unsigned char ZEROS[1024] = {0};
    auto extra = object_getIndexedIvars(obj);
    auto compareSize = std::min(extraSize, sizeof(ZEROS));
    if (memcmp(extra, &ZEROS, compareSize) != 0) {
      if (debug) {
        printf("%p has class %s but has non-zero memory\n", obj, class_getName(cls));
      }
      return nil;
    }
  }

  // Ignore deallocating objects.
  if ([obj _isDeallocating]) {
    return nil;
  }

  return obj;
}

struct FindViableObjcInstancesArgs {
  const std::unordered_set<Class> &classSet;
  std::vector<id, zone_allocator<id>> &instances;
};

static void findViableObjcInstances(vm_range_t range, void *context)
{
  const auto args = reinterpret_cast<FindViableObjcInstancesArgs *>(context);
  id obj = CHLViableObjcInstance(range, args->classSet);
  if (obj != nil) {
    args->instances.push_back(obj);
  }
}

std::vector<id, zone_allocator<id>> CHLScanObjcInstances(const std::unordered_set<Class> &classSet)
{
  std::vector<id, zone_allocator<id>> instances;
  FindViableObjcInstancesArgs args{classSet, instances};
  CHLScanAllocations(&findViableObjcInstances, &args, instances.get_allocator().zone());
  return instances;
}

std::unordered_set<Class> CHLObjcClassSet()
{
  unsigned int count = 0;
  auto classList = objc_copyClassList(&count);
  std::unordered_set<Class> classSet{classList, classList + count, count};
  free(classList);
  return classSet;
}
