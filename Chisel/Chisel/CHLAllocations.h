// Copyright 2004-present Facebook. All Rights Reserved.

#include <malloc/malloc.h>

#if defined(__cplusplus)
extern "C" {
#endif

typedef void (*CHLRangeHandler)(vm_range_t range, void *context);

// Enumerate live allocations in all malloc zones. If callers allocate memory in the handler, those
// allocations should be within the given `sideZone`.
void CHLScanAllocations(CHLRangeHandler handler, void *context, const malloc_zone_t *sideZone);

#if defined(__cplusplus)
}
#endif
