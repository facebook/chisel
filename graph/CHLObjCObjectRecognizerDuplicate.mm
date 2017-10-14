// Copyright 2004-present Facebook. All Rights Reserved.

#if __has_feature(objc_arc)
#error CHLObjCObjectRecognizerCopy.m expects ARC to be disabled.
#endif

#import "CHLObjCObjectRecognizerDuplicate.h"

#include <dlfcn.h>
#include <objc/message.h>
#include <objc/objc.h>
#include <objc/runtime.h>
#include <sstream>
#include <unordered_map>
#include <unordered_set>
#include <vector>

#import <FBBase/fbobjc-internal.h>
#import <FBRetainCycleDetector/FBObjectiveCGraphElement.h>
#import <FBRetainCycleDetector/FBRetainCycleUtils.h>
#import <FBRetainCycleDetector/FBStandardGraphEdgeFilters.h>
#include <mach-o/dyld.h>
#include <mach-o/getsect.h>


#ifndef __LP64__
typedef struct mach_header mach_header_t;
#else
typedef struct mach_header_64 mach_header_t;
#endif

@interface _EXLObjCAllocChecker : NSObject
- (bool)isDefaultAllocUsedByClass:(Class)cls;
@end

@implementation CHLObjCObjectRecognizerDuplicate
{
  std::unordered_set<Class> _classSet;
  _EXLObjCAllocChecker *_allocChecker;
}

- (instancetype)init
{
  if (self = [super init]) {
    unsigned int count = 0;
    _allocChecker = [_EXLObjCAllocChecker new];
    auto classList = objc_copyClassList(&count);
    for (unsigned int i = 0; i < count; ++i) {
      _classSet.insert(classList[i]);
    }
    free(classList);
  }
  return self;
}

- (id)examineRange:(vm_range_t)range
        pointeeList:(NSHashTable<FBObjectiveCGraphElement *> *)pointeeList
            isValid:(BOOL *)isValid
{
  bool checked = false;
  *isValid = NO;

  id object = [self objectAtRange:range];
  if (object == nil) {
    return nil;
  }

  std::vector<Class> classHierarchy;
  Class c = object_getClass(object);
  while (c != Nil) {
    classHierarchy.push_back(c);
    c = class_getSuperclass(c);
  }

  for (auto i = classHierarchy.rbegin(); i != classHierarchy.rend(); ++i) {
    unsigned int count = 0;
    auto ivarList = class_copyIvarList(*i, &count);
    for (unsigned int j = 0; j < count; ++j) {
      auto ivar = ivarList[j];
      auto encoding = ivar_getTypeEncoding(ivar);

      // Validation currently only implemented for ivars of object type. Continue to next ivar.
      if (encoding[0] != _C_ID) {
        continue;
      }

      id ivarObject = object_getIvar(object, ivar);

      // An ivar can be nil, but there's no validation that can be performed on it. Continue to next ivar.
      if (ivarObject == nil) {
        continue;
      }

      checked = true;

      if (malloc_zone_from_ptr(ivarObject) != nullptr) {
        // The ivar's object is on the heap (in a zone), do some checks.
        // Check that the allocation pointed to by the ivar reasonably appears to be an objc class instance.
        vm_range_t rangez = {(vm_address_t)ivarObject, malloc_size(ivarObject)};
        if (ivarObject != [self objectAtRange:rangez]) {
          return nil;
        }

        // Some ivars include a class name (in double quotes following the @ token).
        // If the class name is present, validate that the object referenced by the ivar is in fact an instance of that class.
        // Technically this could be violated intentionally by class implementations.
        auto length = strlen(encoding);
        if (length > 4 && encoding[1] == '"' && encoding[length - 1] == '"') {
          char className[length - 2];
          if (sscanf(encoding, "@\"%s\"", className) == 1) {
            className[length - 3] = NULL;
            if (strchr(className, '<') != nullptr) {
              FBObjectiveCGraphElement *wrappedElement = FBWrapObjectGraphElement(nil, ivarObject, nil);
              [pointeeList addObject:wrappedElement];
              continue;
            }
            if (![ivarObject isKindOfClass:objc_getClass(className)]) {
              return nil;
            }
          }
        }
      }
      else {
        // The ivar's object is not on the heap. See if it's a constant string within the app's binary.
        // NOTE: This would need to be reworked to handle dynamically loaded code.
        Dl_info dl_info;
        dladdr([self class], &dl_info);
        unsigned long size = 0;
        auto start = getsectiondata((mach_header_t *)dl_info.dli_fbase, SEG_DATA, "__cfstring", &size);
        decltype(start) end = start + size;

        if ((void *)ivarObject < start || (void *)ivarObject >= end) {
          return nil;
        }
      }
    }
    free(ivarList);
  }
  if (checked) {
    *isValid = YES;
    return object;
  }
  else {
    return nil;
  }
}

- (BOOL)examineRange:(vm_range_t)range
        deferredList:(NSHashTable<FBObjectiveCGraphElement *> *)deferredList
           validList:(NSHashTable<FBObjectiveCGraphElement *> *)validList
{
  // We may bump into objects that don't provide concrete implementations for functions we might call on them
  // As a result, we're going to go ahead and ignore them and continue
  @try {
    BOOL isValid;
    id object = [self examineRange:range
                       pointeeList:validList
                           isValid:&isValid];

    if (object && [self isWhiteListed:object]) {
      FBObjectiveCGraphElement *wrappedElement = FBWrapObjectGraphElement(nil, object, nil);
      if (isValid) {
        [validList addObject:wrappedElement];
        return YES;
      }
      else {
        [deferredList addObject:wrappedElement];
        return NO;
      }
    }
  }
  @catch (NSException *e) {
    // No op
  }
  return NO;
}

- (void)checkStaticObjects:(NSHashTable<FBObjectiveCGraphElement *> *)deferredList
               pointeeList:(NSHashTable<FBObjectiveCGraphElement *> *)pointeeList
{
  const uint32_t imageCount = _dyld_image_count();
  for (uint32_t imageIndex = 0; imageIndex < imageCount; ++imageIndex) {
    const mach_header_t *header = (const mach_header_t *)_dyld_get_image_header(imageIndex);
    unsigned long size = 0;
    void **elements = (void **)getsectiondata(header, SEG_DATA, SECT_BSS, &size);
    const unsigned long elementCount = size / sizeof(void *);
    for (unsigned long elementIndex = 0; elementIndex < elementCount; ++elementIndex) {
      void *element = elements[elementIndex];
      if (malloc_zone_from_ptr(element)) {
        vm_range_t rangez = { (vm_address_t)element, (vm_size_t)malloc_size(element) };

        // Check range using the same way as heap allocations are checked.
        [self examineRange:rangez deferredList:deferredList validList:pointeeList];
      }
    }
  }
}

- (BOOL)isWhiteListed:(id)object
{
  const char *objectClassName = object_getClassName(object);
  if (!strstr(objectClassName, "NSCF")
      && !strstr(objectClassName, "NSTaggedPointerStringCStringContainer")
      && !strstr(objectClassName, "NSZombie")) {
    return YES;
  }
  return NO;
}

- (id)objectAtRange:(vm_range_t)range
{
  assert(range.size >= sizeof(objc_object));

  const id object = (id)range.address;
  const Class cls = object_getClass(object);

  if (_classSet.find(cls) == _classSet.end()) {
    return nil;
  }

  const auto goodInstanceSize = malloc_good_size(class_getInstanceSize(cls));
  if (range.size < goodInstanceSize) {
    return nil;
  }

  if (range.size > goodInstanceSize && [_allocChecker isDefaultAllocUsedByClass:cls]) {
    return nil;
  }

  auto isDeallocating = reinterpret_cast<BOOL (*)(id, SEL)>(objc_msgSend);

  if ([self isWhiteListed:object] && isDeallocating(object, sel_registerName("_isDeallocating"))) {
    return nil;
  }
  return object;
}

@end

@implementation _EXLObjCAllocChecker
{
  IMP _defaultAllocWithZone;
  IMP _defaultAlloc;
  std::unordered_map<Class, bool> _cache;
}

- (instancetype)init
{
  self = [super init];
  if (self != nil) {
    const Class objectMetaClass = objc_getMetaClass("NSObject");
    _defaultAllocWithZone = class_getMethodImplementation(objectMetaClass, @selector(allocWithZone:));
    _defaultAlloc = class_getMethodImplementation(objectMetaClass, @selector(alloc));
  }
  return self;
}

- (bool)isDefaultAllocUsedByClass:(Class)cls
{
  const auto match = _cache.find(cls);
  if (match != _cache.end()) {
    return match->second;
  }

  const Class metaClass = object_getClass(cls);
  const bool usesDefaultAlloc =
  class_getMethodImplementation(metaClass, @selector(allocWithZone:)) == _defaultAllocWithZone &&
  class_getMethodImplementation(metaClass, @selector(alloc)) == _defaultAlloc;

  return _cache[cls] = usesDefaultAlloc;
}

@end
