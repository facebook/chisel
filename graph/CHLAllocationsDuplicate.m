// Copyright 2004-present Facebook. All Rights Reserved.

#if __has_feature(objc_arc)
#error CHLAllocations.m expects ARC to be disabled.
#endif

#import "CHLAllocationsDuplicate.h"

// See vm_range_recorder_t
static void enumerateRanges(task_t, void *, unsigned, vm_range_t *, unsigned);

static kern_return_t reader(__unused task_t remote_task, vm_address_t remote_address, __unused vm_size_t size, void **local_memory)
{
  *local_memory = (void *)remote_address;
  return KERN_SUCCESS;
}

void duplicateCHLEnumerateAllocationsWithBlock(void (^block)(vm_range_t))
{
  /*
   * === Overview ===
   *
   * To enumerate the set of live memory allocations ("ranges"), the pseudocode might look like:
   *
   *     for zone in all_zones()
   *       for range in zone->ranges
   *         callback(range)
   *
   * Unfortunately, the memory allocations within a zone are not exposed directly, so the inner loop is not possible.
   * Instead, malloc zones provide a function that loops over the allocations, calling a callback function for each one.
   *
   * Note:
   *
   * Both `malloc_get_all_zones` and `vm_range_recorder_t` callback functions take a `task_t` parameter. However it
   * turns out it can be `NULL` provided it's not used by the `memory_reader_t` and `vm_range_recorder_t` functions.
   */

  // Get a reference to the array of zones.
  vm_address_t *zones;
  unsigned int zoneCount;
  malloc_get_all_zones(TASK_NULL, reader, &zones, &zoneCount);

  // Outer loop over the zones.
  for (unsigned int i = 0; i < zoneCount; i++) {
    // While `zones` is typed as `vm_address_t *` for type checking purposes, these addresses are just pointers to
    // `malloc_zone_t` structs. Thus `vm_address_t` and `malloc_zone_t *` are used interchangably here.
    malloc_zone_t *zone = (malloc_zone_t *)zones[i];

    // Inner loop over the zone's memory allocations.
    zone->introspect->enumerator(TASK_NULL, (__bridge void *)(block), MALLOC_PTR_IN_USE_RANGE_TYPE, (vm_address_t)zone, reader, enumerateRanges);
  }
}

// This function is called with an array of memory allocations, which are represented as `vm_range_t` structs.
static void enumerateRanges(__unused task_t task, void *context, __unused unsigned type, vm_range_t *ranges, unsigned rangeCount)
{
  void (^block)(vm_range_t) = (__bridge void (^)(vm_range_t))(context);

  for (unsigned int i = 0; i < rangeCount; i++) {
    block(ranges[i]);
  }
}
