// Copyright 2004-present Facebook. All Rights Reserved.

#if defined(__cplusplus)

#include <malloc/malloc.h>
#include <unordered_set>
#include <vector>

#include "zone_allocator.h"

// Create a set containing all known Classes.
std::unordered_set<Class> CHLObjcClassSet();

// Enumerates the heap and returns all objects that appear to be legitimate.
std::vector<id, zone_allocator<id>> CHLScanObjcInstances(const std::unordered_set<Class> &classSet);

// Performs a number of heuristic checks on the memory range, to determine if the memory appears to
// be a viable Objective-C object.
id CHLViableObjcInstance(vm_range_t range, const std::unordered_set<Class> &classSet);

#endif
