// Copyright 2004-present Facebook. All Rights Reserved.

#import "CHLObjcInstanceCommands.h"

#include <objc/runtime.h>
#include <vector>

#import <CoreFoundation/CoreFoundation.h>
#import <Foundation/Foundation.h>

#import "CHLObjcInstances.h"
#import "CHLPredicateTools.h"
#include "zone_allocator.h"

#if __has_feature(objc_arc)
#error Disable ARC for this file
#endif

struct IsValidArgs {
  const std::unordered_set<Class> &classSet;
  bool isValid = true;
};

static void isValidObject(const void *value, void *context)
{
  const auto args = reinterpret_cast<IsValidArgs *>(context);
  if (!args->isValid) {
    return;
  }

  vm_range_t range = {(vm_address_t)value, malloc_size(value)};
  if (CHLViableObjcInstance(range, args->classSet) == nil) {
    args->isValid = false;
  }
}

static void isValidKeyValue(const void *key, const void *value, void *context)
{
  const auto args = reinterpret_cast<IsValidArgs *>(context);
  isValidObject(key, context);
  if (args->isValid) {
    isValidObject(value, context);
  }
}

static bool predicatePrecheck(id obj, const std::unordered_set<Class> &classSet)
{
  IsValidArgs args{classSet};

  if ([obj isKindOfClass:objc_getClass("__NSCFDictionary")]) {
    CFDictionaryApplyFunction((CFDictionaryRef)obj, &isValidKeyValue, &args);
  } else if ([obj isKindOfClass:objc_getClass("__NSCFSet")]) {
    CFSetApplyFunction((CFSetRef)obj, &isValidObject, &args);
  } else {
    // Skip classes containing NSPlaceholder.
    // TODO: Figure out better way to ignore invalid instances.
    char *name = (char *)object_getClassName(obj);
    while (*name == '_') ++name;
    if (strncmp(name, "NSPlaceholder", sizeof("NSPlaceholder") - 1) == 0) {
      args.isValid = false;
    }
  }

  if (!args.isValid && getenv("FINDINSTANCES_DEBUG")) {
    printf("%p has class %s but contains non objc data\n", obj, object_getClassName(obj));
  }

  return args.isValid;
}

static void printObject(id obj, NSSet *keyPaths) {
  printf("<%s: %p", object_getClassName(obj), obj);
  for (NSString *keyPath in keyPaths) {
    printf("; %s = %s", keyPath.UTF8String, [[obj valueForKeyPath:keyPath] description].UTF8String);
  }
  printf(">\n");
}

static bool objectIsMatch(NSPredicate *predicate, id obj, const std::unordered_set<Class> &classSet)
{
  if (!predicate) {
    return true;
  }

  bool debug = getenv("FINDINSTANCES_DEBUG");

  if (!predicatePrecheck(obj, classSet)) {
    if (debug) {
      printf("%p has class %s but has non objc contents\n", obj, object_getClassName(obj));
    }
    return false;
  }

  @try {
    return [predicate evaluateWithObject:obj];
  } @catch (...) {
    if (debug) {
      printf("%p has class %s but failed predicate evaluation\n", obj, object_getClassName(obj));
    }
    return false;
  }
}

// Function reimplementation of +[NSObject isSubclassOf:] to avoid the objc runtime side
// effects that can happen when calling methods, like realizing classes, +initialize, etc.
static bool isSubclassOf(Class base, Class target)
{
  for (auto cls = base; cls != Nil; cls = class_getSuperclass(cls)) {
    if (cls == target) {
      return true;
    }
  }
  return false;
}

// Function reimplementation of +[NSObject conformsToProtocol:] to avoid the objc runtime side
// effects that can happen when calling methods, like realizing classes, +initialize, etc.
static bool conformsToProtocol(Class base, Protocol *protocol)
{
  for (auto cls = base; cls != Nil; cls = class_getSuperclass(cls)) {
    if (class_conformsToProtocol(cls, protocol)) {
      return true;
    }
  }
  return false;
}

void PrintInstances(const char *type, const char *pred)
{
  NSPredicate *predicate = nil;
  if (pred != nullptr && *pred != '\0') {
    @try {
      predicate = [NSPredicate predicateWithFormat:@(pred)];
    } @catch (NSException *e) {
      printf("Error: Invalid predicate; %s\n", [e reason].UTF8String);
      return;
    }
  }

  const std::unordered_set<Class> objcClasses = CHLObjcClassSet();
  std::unordered_set<Class> matchClasses;

  Protocol *protocol = objc_getProtocol(type);
  if (protocol != nullptr && strcmp("NSObject", type) != 0) {
    for (auto cls : objcClasses) {
      if (conformsToProtocol(cls, protocol)) {
        matchClasses.insert(cls);
      }
    }
  }

  if (type[0] == '*') {
    ++type;
    Class cls = objc_getClass(type);
    if (cls != nullptr) {
      matchClasses.insert(cls);
    }
  } else if (Class kind = objc_getClass(type)) {
    // This could be optimized for type == "NSObject", but it won't be a typical search.
    for (auto cls : objcClasses) {
      if (isSubclassOf(cls, kind)) {
        matchClasses.insert(cls);
      }
    }
  }

  if (matchClasses.empty()) {
    // TODO: Accept name of library/module, and list instances of classes defined there.
    printf("Unknown type: %s\n", type);
    return;
  }

  NSSet *keyPaths = CHLVariableKeyPaths(predicate);

  std::vector<id, zone_allocator<id>> instances = CHLScanObjcInstances(matchClasses);
  unsigned int matches = 0;

  for (id obj : instances) {
    if (objectIsMatch(predicate, obj, objcClasses)) {
      ++matches;
      printObject(obj, keyPaths);
    }
  }

  if (matches > 1) {
    printf("%d matches\n", matches);
  }
}
