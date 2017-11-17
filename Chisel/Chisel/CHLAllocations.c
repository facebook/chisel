// Copyright 2004-present Facebook. All Rights Reserved.

#include "CHLAllocations.h"

static kern_return_t reader(__unused task_t remote_task, vm_address_t remote_address, __unused vm_size_t size, void **local_memory)
{
  *local_memory = (void *)remote_address;
  return KERN_SUCCESS;
}

typedef struct {
  CHLRangeHandler handler;
  void *context;
} RangeEnumeratorArgs;

static void rangeEnumerator(__unused task_t task, void *context, __unused unsigned type, vm_range_t *ranges, unsigned int count)
{
  const RangeEnumeratorArgs *args = (RangeEnumeratorArgs *)context;
  for (unsigned int i = 0; i < count; ++i) {
    args->handler(ranges[i], args->context);
  }
}

void CHLScanAllocations(CHLRangeHandler handler, void *context, const malloc_zone_t *sideZone)
{
  vm_address_t *zones;
  unsigned int count;
  malloc_get_all_zones(TASK_NULL, &reader, &zones, &count);

  RangeEnumeratorArgs args = {handler, context};

  for (unsigned int i = 0; i < count; ++i) {
    malloc_zone_t *zone = (malloc_zone_t *)zones[i];
    if (zone != sideZone) {
      zone->introspect->enumerator(TASK_NULL, &args, MALLOC_PTR_IN_USE_RANGE_TYPE, (vm_address_t)zone, reader, rangeEnumerator);
    }
  }
}
