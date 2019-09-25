// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
//
// This source code is licensed under the MIT license found in the
// LICENSE file in the root directory of this source tree.

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
